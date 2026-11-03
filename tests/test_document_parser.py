
import pytest
import pymupdf

from app.services.document_parser import (
    extract_text_from_txt,
    extract_text_from_pdf,
    extract_document_text
)


def test_extract_text_from_txt():
    content = "This is a sample document for testing."
    file_bytes = content.encode("utf-8")

    result = extract_text_from_txt(file_bytes)

    assert result == content


def test_extract_text_from_txt_with_unicode():
    content = "Python, AI, and data science — नेपाल"
    file_bytes = content.encode("utf-8")

    result = extract_text_from_txt(file_bytes)

    assert result == content


def test_extract_text_from_pdf():
    pdf = pymupdf.open()

    page = pdf.new_page()
    page.insert_text(
        (72, 72),
        "This is a sample PDF document."
    )

    file_bytes = pdf.tobytes()
    pdf.close()

    result = extract_text_from_pdf(file_bytes)

    assert "This is a sample PDF document." in result


def test_extract_document_text_for_txt():
    content = "Testing TXT document extraction."
    file_bytes = content.encode("utf-8")

    result = extract_document_text(
        "sample.txt",
        file_bytes
    )

    assert result == content


def test_extract_document_text_for_pdf():
    pdf = pymupdf.open()

    page = pdf.new_page()
    page.insert_text(
        (72, 72),
        "Testing PDF document extraction."
    )

    file_bytes = pdf.tobytes()
    pdf.close()

    result = extract_document_text(
        "sample.pdf",
        file_bytes
    )

    assert "Testing PDF document extraction." in result


def test_unsupported_file_extension():
    with pytest.raises(ValueError):
        extract_document_text(
            "sample.docx",
            b"Some document content"
        )
