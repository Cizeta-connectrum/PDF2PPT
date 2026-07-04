"""OCR-based fallback text extraction for PDF pages that contain no native
text at all (e.g. a page that is really just a flattened screenshot/scan).

Requires the Tesseract OCR engine to be installed on the host system
(separately from the Python package):

  - macOS:  brew install tesseract tesseract-lang
  - Debian/Ubuntu: apt install tesseract-ocr tesseract-ocr-jpn

pytesseract only calls out to that binary; it does not bundle it.
"""
from __future__ import annotations

from PIL import Image, ImageDraw
import pytesseract

OCR_LANG = "jpn+eng"
MIN_CONFIDENCE = 40

_availability_checked = False
_available = False


class TesseractUnavailableError(RuntimeError):
    pass


def is_available() -> bool:
    global _availability_checked, _available
    if not _availability_checked:
        try:
            pytesseract.get_tesseract_version()
            _available = True
        except Exception:
            _available = False
        _availability_checked = True
    return _available


def _foreground_color(
    img: Image.Image, box, bg: tuple[int, int, int], top_fraction: float = 0.25
) -> tuple[int, int, int]:
    """Estimate the text (ink) color inside `box` as the average of the
    pixels furthest (by color distance) from the already-known background
    color `bg`. Using distance-from-background rather than "darker than
    average" correctly handles both dark text on a light background AND
    light/white text on a dark background (e.g. title banners).
    """
    crop = img.crop(box).convert("RGB")
    pixels = list(crop.getdata())
    if not pixels:
        return (0, 0, 0)

    def dist2(p: tuple[int, int, int]) -> int:
        return (p[0] - bg[0]) ** 2 + (p[1] - bg[1]) ** 2 + (p[2] - bg[2]) ** 2

    scored = sorted(pixels, key=dist2, reverse=True)
    if dist2(scored[0]) == 0:
        # No contrast at all against the background (shouldn't normally
        # happen for real text) - fall back to a plain average.
        fg_pixels = pixels
    else:
        take = max(1, int(len(scored) * top_fraction))
        fg_pixels = scored[:take]
    n = len(fg_pixels)
    return (
        sum(p[0] for p in fg_pixels) // n,
        sum(p[1] for p in fg_pixels) // n,
        sum(p[2] for p in fg_pixels) // n,
    )


def _background_color(img: Image.Image, box, margin: int = 4) -> tuple[int, int, int]:
    left, top, right, bottom = box
    width, height = img.size
    outer = (
        max(left - margin, 0),
        max(top - margin, 0),
        min(right + margin, width),
        min(bottom + margin, height),
    )
    if outer[2] <= outer[0] or outer[3] <= outer[1]:
        return (255, 255, 255)
    crop = img.crop(outer).convert("RGB")
    inner = (left - outer[0], top - outer[1], right - outer[0], bottom - outer[1])
    border_pixels = [
        crop.getpixel((x, y))
        for x in range(crop.width)
        for y in range(crop.height)
        if not (inner[0] <= x < inner[2] and inner[1] <= y < inner[3])
    ]
    if not border_pixels:
        return (255, 255, 255)
    n = len(border_pixels)
    return (
        sum(p[0] for p in border_pixels) // n,
        sum(p[1] for p in border_pixels) // n,
        sum(p[2] for p in border_pixels) // n,
    )


def extract_ocr_spans(img: Image.Image, dpi: int) -> list[dict]:
    """Run OCR on `img` (rendered at `dpi`), returning line-level spans with
    a PDF-point bbox, recognized text, an estimated font size/color. As a
    side effect, paints over each detected text region on `img` in place
    using the sampled local background color, so the caller can embed the
    now text-free `img` as a clean background.
    """
    if not is_available():
        raise TesseractUnavailableError(
            "Tesseract OCRが見つかりません。OCRを使うにはインストールが必要です: "
            "macOSは `brew install tesseract tesseract-lang`、"
            "Debian/Ubuntuは `apt install tesseract-ocr tesseract-ocr-jpn` を実行してください。"
        )

    data = pytesseract.image_to_data(img, lang=OCR_LANG, output_type=pytesseract.Output.DICT)

    lines: dict[tuple, dict] = {}
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1
        if not text or conf < MIN_CONFIDENCE:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        left, top = data["left"][i], data["top"][i]
        right, bottom = left + data["width"][i], top + data["height"][i]
        line = lines.setdefault(
            key, {"words": [], "left": left, "top": top, "right": right, "bottom": bottom}
        )
        line["words"].append(text)
        line["left"] = min(line["left"], left)
        line["top"] = min(line["top"], top)
        line["right"] = max(line["right"], right)
        line["bottom"] = max(line["bottom"], bottom)

    zoom = dpi / 72.0
    draw = ImageDraw.Draw(img)
    spans = []
    for line in lines.values():
        box = (line["left"], line["top"], line["right"], line["bottom"])
        bg = _background_color(img, box)
        fg = _foreground_color(img, box, bg)
        draw.rectangle(box, fill=bg)
        spans.append(
            {
                "text": " ".join(line["words"]),
                "bbox": tuple(v / zoom for v in box),
                "size": max((box[3] - box[1]) / zoom * 0.8, 6),
                "color": fg,
                "flags": 0,
                "font": "",
            }
        )
    return spans
