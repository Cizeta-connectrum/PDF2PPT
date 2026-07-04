"""Diagnose why editable-mode text extraction might be producing no visible
text spans for a given PDF, without needing to share the PDF's actual
content. Run:

    python3 scripts/diagnose_pdf.py path/to/file.pdf

and paste the printed report back for troubleshooting.
"""
import sys

import fitz

INVISIBLE_RENDER_MODES = (3, 7)


def main(path: str) -> None:
    doc = fitz.open(path)
    print(f"pages: {doc.page_count}")
    print(f"is_pdf: {doc.is_pdf}  needs_pass: {doc.needs_pass}")

    for i, page in enumerate(doc):
        raw_text = page.get_text()
        text_dict_blocks = page.get_text("dict").get("blocks", [])
        text_blocks = [b for b in text_dict_blocks if b.get("type") == 0]
        image_blocks = [b for b in text_dict_blocks if b.get("type") == 1]

        try:
            traces = page.get_texttrace()
        except Exception as exc:
            traces = None
            trace_error = repr(exc)
        else:
            trace_error = None

        visible_spans = 0
        render_modes = set()
        sample_text = ""
        if traces is not None:
            for tr in traces:
                render_modes.add(tr.get("type"))
                if tr.get("type") in INVISIBLE_RENDER_MODES:
                    continue
                chars = tr.get("chars", [])
                s = "".join(chr(c[0]) for c in chars if c[0] > 0)
                if s.strip():
                    visible_spans += 1
                    if not sample_text:
                        sample_text = s[:40]

        print(f"--- page {i + 1} ---")
        print(f"  rotation: {page.rotation}  rect: {page.rect}")
        print(f"  get_text() length: {len(raw_text)}")
        print(f"  get_text(dict) text-blocks: {len(text_blocks)}  image-blocks: {len(image_blocks)}")
        if trace_error:
            print(f"  get_texttrace() ERROR: {trace_error}")
        else:
            print(f"  get_texttrace() groups: {len(traces)}  render_modes seen: {sorted(render_modes)}")
            print(f"  visible text spans (non-empty, non-invisible): {visible_spans}")
            if sample_text:
                print(f"  sample extracted text: {sample_text!r}")

        fonts = page.get_fonts(full=True)
        # each entry: (xref, ext, type, basefont, name, encoding, ...)
        print(f"  fonts on page (type, basefont, encoding): {[(f[2], f[3], f[5]) for f in fonts]}")

    doc.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/diagnose_pdf.py path/to/file.pdf")
        sys.exit(1)
    main(sys.argv[1])
