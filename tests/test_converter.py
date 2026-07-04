import os
import sys
import tempfile

import fitz
import pytest
from pptx import Presentation

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from converter import convert_pdf_to_pptx  # noqa: E402


@pytest.fixture
def sample_pdf(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=612, height=792)  # US Letter
        page.insert_text((72, 72), f"Page {i + 1} heading", fontsize=24)
        page.insert_text((72, 120), "Some body text to verify extraction.", fontsize=12)
        page.draw_rect(fitz.Rect(72, 200, 300, 260), color=(0, 0, 1), fill=(0.8, 0.9, 1))
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


def test_image_mode(sample_pdf, tmp_path):
    out_path = tmp_path / "out_image.pptx"
    result = convert_pdf_to_pptx(sample_pdf, str(out_path), mode="image")
    assert result.page_count == 3
    assert out_path.exists()

    prs = Presentation(str(out_path))
    assert len(prs.slides.__iter__.__self__._sldIdLst) == 3
    for slide in prs.slides:
        pictures = [s for s in slide.shapes if s.shape_type == 13]
        assert len(pictures) == 1


def test_editable_mode(sample_pdf, tmp_path):
    out_path = tmp_path / "out_editable.pptx"
    result = convert_pdf_to_pptx(sample_pdf, str(out_path), mode="editable")
    assert result.page_count == 3
    assert out_path.exists()

    prs = Presentation(str(out_path))
    slide_count = sum(1 for _ in prs.slides)
    assert slide_count == 3

    first_slide = next(iter(prs.slides))
    texts = []
    for shape in first_slide.shapes:
        if shape.has_text_frame:
            texts.append(shape.text_frame.text)
    joined = " ".join(texts)
    assert "Page 1 heading" in joined
    assert "body text" in joined


def test_invalid_mode(sample_pdf, tmp_path):
    out_path = tmp_path / "out.pptx"
    with pytest.raises(ValueError):
        convert_pdf_to_pptx(sample_pdf, str(out_path), mode="bogus")
