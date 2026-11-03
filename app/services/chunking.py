
from app.core.config import settings


def fixed_size_chunking(
    text: str,
    chunk_size: int,
    chunk_overlap: int
) -> list[str]:
    """
    Split text into fixed-size chunks with character overlap.
    """

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("Invalid chunk overlap.")

    chunks = []
    start = 0
    step = chunk_size - chunk_overlap

    while start < len(text):
        chunk = text[start:start + chunk_size].strip()

        if chunk:
            chunks.append(chunk)

        start += step

    return chunks


def recursive_chunking(
    text: str,
    chunk_size: int,
    chunk_overlap: int
) -> list[str]:
    """
    Split text recursively using paragraph, newline, sentence,
    and word separators while maintaining chunk size limits.
    """

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("Invalid chunk overlap.")

    # Reserve space for overlap and its separating space.
    raw_chunk_limit = (
        chunk_size - chunk_overlap - 1
        if chunk_overlap > 0
        else chunk_size
    )

    separators = ["\n\n", "\n", ". ", " ", ""]

    def split_text(
        content: str,
        separator_index: int = 0
    ) -> list[str]:

        if not content.strip():
            return []

        if len(content) <= raw_chunk_limit:
            return [content]

        if separator_index >= len(separators):
            return fixed_size_chunking(
                content,
                raw_chunk_limit,
                0
            )

        separator = separators[separator_index]

        if not separator:
            return fixed_size_chunking(
                content,
                raw_chunk_limit,
                0
            )

        parts = content.split(separator)

        units = [
            part + separator for part in parts[:-1]
        ] + [parts[-1]]

        chunks = []
        current = ""

        for unit in units:

            if not unit:
                continue

            if len(unit) > raw_chunk_limit:

                if current.strip():
                    chunks.append(current.strip())
                    current = ""

                chunks.extend(
                    split_text(
                        unit,
                        separator_index + 1
                    )
                )

                continue

            candidate = current + unit

            if len(candidate) <= raw_chunk_limit:
                current = candidate

            else:
                if current.strip():
                    chunks.append(current.strip())

                current = unit

        if current.strip():
            chunks.append(current.strip())

        return chunks

    raw_chunks = split_text(text)

    # Add overlap from the previous chunk.
    chunks = []

    for index, chunk in enumerate(raw_chunks):

        if index > 0 and chunk_overlap > 0:

            previous = raw_chunks[index - 1]

            overlap_text = previous[-chunk_overlap:]

            # Avoid starting in the middle of a word.
            if " " in overlap_text:
                overlap_text = overlap_text.split(" ", 1)[1]

            if overlap_text:
                chunk = overlap_text + " " + chunk

        # Final safety check.
        if len(chunk) > chunk_size:
            chunk = chunk[:chunk_size]

        chunks.append(chunk)

    return chunks


def chunk_document(
    text: str,
    strategy: str = "recursive"
) -> list[str]:
    """
    Select the required document chunking strategy.
    """

    if not text.strip():
        return []

    if strategy == "fixed":
        return fixed_size_chunking(
            text,
            settings.chunk_size,
            settings.chunk_overlap
        )

    elif strategy == "recursive":
        return recursive_chunking(
            text,
            settings.chunk_size,
            settings.chunk_overlap
        )

    else:
        raise ValueError(
            "Invalid chunking strategy. "
            "Choose 'fixed' or 'recursive'."
        )
