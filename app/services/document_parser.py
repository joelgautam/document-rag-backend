import pymupdf


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF document.
    """

    extracted_pages = []

    with pymupdf.open(stream=file_bytes, filetype="pdf") as pdf:

        for page in pdf:
            page_text = page.get_text()

            if page_text.strip():
                extracted_pages.append(page_text)

    return "\n".join(extracted_pages)


def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Extract text from a TXT document.
    """

    return file_bytes.decode("utf-8", errors="replace")


def extract_document_text(filename: str, file_bytes: bytes) -> str:
    """
    Identify the document type and extract its text.
    """

    extension = filename.lower().rsplit(".", 1)[-1]

    if extension == "pdf":
        return extract_text_from_pdf(file_bytes)

    elif extension == "txt":
        return extract_text_from_txt(file_bytes)

    else:
        raise ValueError("Only PDF and TXT files are supported.")