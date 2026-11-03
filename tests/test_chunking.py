
import pytest

from app.services.chunking import (
    fixed_size_chunking,
    recursive_chunking,
    chunk_document
)


def test_fixed_chunking_respects_maximum_size():
    text = "Python is useful for data science. " * 100

    chunks = fixed_size_chunking(text, 800, 120)

    assert len(chunks) > 1
    assert all(len(chunk) <= 800 for chunk in chunks)


def test_recursive_chunking_respects_maximum_size():
    text = "Python is useful for data science. " * 100

    chunks = recursive_chunking(text, 800, 120)

    assert len(chunks) > 1
    assert all(len(chunk) <= 800 for chunk in chunks)


def test_empty_document_returns_empty_list():
    assert chunk_document("") == []
    assert chunk_document("   ") == []


def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        fixed_size_chunking("Hello world", 0, 0)

    with pytest.raises(ValueError):
        recursive_chunking("Hello world", 0, 0)


def test_invalid_chunk_overlap():
    with pytest.raises(ValueError):
        fixed_size_chunking("Hello world", 800, 800)

    with pytest.raises(ValueError):
        recursive_chunking("Hello world", 800, 800)


def test_invalid_chunking_strategy():
    with pytest.raises(ValueError):
        chunk_document("Python is useful", strategy="invalid")
