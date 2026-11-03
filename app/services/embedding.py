
from functools import lru_cache

from fastembed import TextEmbedding


# Name of the local embedding model
MODEL_NAME = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    """
    Load the embedding model once and reuse it.
    """

    return TextEmbedding(model_name=MODEL_NAME)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Convert multiple text strings into numerical vectors.
    """

    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.embed(texts)

    return [
        embedding.tolist()
        for embedding in embeddings
    ]


def generate_embedding(text: str) -> list[float]:
    """
    Convert a single text string into a numerical vector.
    """

    if not text.strip():
        raise ValueError("Text cannot be empty.")

    return generate_embeddings([text])[0]
