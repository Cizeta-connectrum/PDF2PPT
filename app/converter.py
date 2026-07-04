"""PDF -> PPTX conversion core.

Two modes are supported:

- "image": each PDF page is rasterized at high resolution and placed as a
  full-bleed picture on its own slide. This reproduces the PDF's appearance
  exactly (fonts, vector art, layout) at the cost of the text no longer
  being editable in PowerPoint.
- "editable": each page is rasterized the same way, but the original text
  is first surgically removed from the page (via PDF redaction) so the
  background image keeps every non-text visual element (vector art,
  photos, gradients) while real, independently editable PowerPoint text
  boxes are overlaid matching the extracted text's position/font/size/color.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import fitz  # PyMuPDF
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

EMU_PER_POINT = 12700
DEFAULT_DPI = 200

# PyMuPDF span flag bits (see fitz docs: font flags bitfield)
FLAG_ITALIC = 1 << 1
FLAG_BOLD = 1 << 4


@dataclass
class ConversionResult:
    page_count: int
    mode: str


def _pt_to_emu(value_pt: float) -> int:
    return int(round(value_pt * EMU_PER_POINT))


def _fit_size(src_w: float, src_h: float, box_w: float, box_h: float) -> tuple[float, float, float, float]:
    """Return (left, top, width, height) to fit src into box, centered, preserving aspect ratio."""
    src_ratio = src_w / src_h
    box_ratio = box_w / box_h
    if src_ratio > box_ratio:
        width = box_w
        height = box_w / src_ratio
    else:
        height = box_h
        width = box_h * src_ratio
    left = (box_w - width) / 2
    top = (box_h - height) / 2
    return left, top, width, height


def convert_image_mode(doc: fitz.Document, prs: Presentation, dpi: int = DEFAULT_DPI) -> None:
    first_page = doc[0]
    slide_w_pt = first_page.rect.width
    slide_h_pt = first_page.rect.height
    prs.slide_width = _pt_to_emu(slide_w_pt)
    prs.slide_height = _pt_to_emu(slide_h_pt)

    blank_layout = prs.slide_layouts[6]
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    for page in doc:
        slide = prs.slides.add_slide(blank_layout)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_bytes = pix.tobytes("png")
        img_stream = io.BytesIO(img_bytes)

        left, top, width, height = _fit_size(
            page.rect.width, page.rect.height, slide_w_pt, slide_h_pt
        )
        slide.shapes.add_picture(
            img_stream,
            _pt_to_emu(left),
            _pt_to_emu(top),
            width=_pt_to_emu(width),
            height=_pt_to_emu(height),
        )


# PDF text render modes (see PDF spec 9.3.6 "Text Rendering Mode", as
# reported by fitz.Page.get_texttrace()'s "type" field). 3 = invisible fill
# (used for e.g. OCR text layers over a scanned image), 7 = invisible clip.
INVISIBLE_RENDER_MODES = (3, 7)


def _extract_visible_text_spans(page: fitz.Page) -> list[dict]:
    """Collect visible text spans (bbox/font/size/color/flags/text), skipping
    invisible render modes so OCR-only text layers are left untouched."""
    spans = []
    for trace in page.get_texttrace():
        if trace.get("type") in INVISIBLE_RENDER_MODES:
            continue
        text = "".join(chr(ch[0]) for ch in trace.get("chars", []))
        if not text.strip():
            continue
        r, g, b = trace.get("color", (0, 0, 0))
        spans.append(
            {
                "text": text,
                "bbox": trace["bbox"],
                "font": trace.get("font", ""),
                "size": trace.get("size", 12),
                "flags": trace.get("flags", 0),
                "color": (int(r * 255), int(g * 255), int(b * 255)),
            }
        )
    return spans


def _add_text_span_box(slide, span: dict) -> None:
    x0, y0, x1, y1 = span["bbox"]
    width = max(x1 - x0, 1)
    height = max(y1 - y0, 1)
    # Pad the box slightly so text isn't clipped by PowerPoint's own metrics.
    pad_x = 2
    pad_y = 1
    textbox = slide.shapes.add_textbox(
        _pt_to_emu(x0 - pad_x),
        _pt_to_emu(y0 - pad_y),
        _pt_to_emu(width + 2 * pad_x),
        _pt_to_emu(height + 2 * pad_y),
    )
    tf = textbox.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = span["text"]
    font = run.font
    font.size = Pt(max(span["size"], 1))
    flags = span.get("flags", 0)
    font.bold = bool(flags & FLAG_BOLD)
    font.italic = bool(flags & FLAG_ITALIC)
    r, g, b = span.get("color", (0, 0, 0))
    font.color.rgb = RGBColor(r, g, b)
    fontname = span.get("font", "")
    if "+" in fontname:
        fontname = fontname.split("+", 1)[1]
    fontname = fontname.split(",")[0].split("-")[0].strip()
    if fontname:
        font.name = fontname


def convert_editable_mode(doc: fitz.Document, prs: Presentation, dpi: int = DEFAULT_DPI) -> None:
    """Rebuild each page as a background image (all vector art, photos and
    gradients rasterized, exactly as in image mode) with the original text
    content surgically removed via PDF redaction, then overlay real,
    independently editable PowerPoint text boxes matching the extracted
    text's position/font/size/color. This keeps full visual fidelity for
    everything that isn't text while making the text itself editable.
    """
    first_page = doc[0]
    slide_w_pt = first_page.rect.width
    slide_h_pt = first_page.rect.height
    prs.slide_width = _pt_to_emu(slide_w_pt)
    prs.slide_height = _pt_to_emu(slide_h_pt)

    blank_layout = prs.slide_layouts[6]
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    for page in doc:
        spans = _extract_visible_text_spans(page)

        for span in spans:
            page.add_redact_annot(fitz.Rect(span["bbox"]), fill=None)
        if spans:
            page.apply_redactions(images=0, graphics=0, text=0)

        slide = prs.slides.add_slide(blank_layout)
        left, top, scale_w, scale_h = _fit_size(
            page.rect.width, page.rect.height, slide_w_pt, slide_h_pt
        )
        sx = scale_w / page.rect.width
        sy = scale_h / page.rect.height

        pix = page.get_pixmap(matrix=matrix, alpha=False)
        slide.shapes.add_picture(
            io.BytesIO(pix.tobytes("png")),
            _pt_to_emu(left),
            _pt_to_emu(top),
            width=_pt_to_emu(scale_w),
            height=_pt_to_emu(scale_h),
        )

        for span in spans:
            x0, y0, x1, y1 = span["bbox"]
            scaled_span = dict(
                span,
                bbox=(
                    left + x0 * sx,
                    top + y0 * sy,
                    left + x1 * sx,
                    top + y1 * sy,
                ),
                size=span["size"] * min(sx, sy),
            )
            _add_text_span_box(slide, scaled_span)


def convert_pdf_to_pptx(pdf_path: str, pptx_path: str, mode: str = "image", dpi: int = DEFAULT_DPI) -> ConversionResult:
    if mode not in ("image", "editable"):
        raise ValueError(f"Unknown mode: {mode}")

    doc = fitz.open(pdf_path)
    try:
        if doc.page_count == 0:
            raise ValueError("PDF has no pages")
        prs = Presentation()
        if mode == "image":
            convert_image_mode(doc, prs, dpi=dpi)
        else:
            convert_editable_mode(doc, prs, dpi=dpi)
        prs.save(pptx_path)
        return ConversionResult(page_count=doc.page_count, mode=mode)
    finally:
        doc.close()
