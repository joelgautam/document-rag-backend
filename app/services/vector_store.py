
from uuid import uuid4

from qdrant_client import QdrantClient, models

from app.core.config import settings


VECTOR_SIZE = 384


# Connect to Qdrant
client = QdrantClient(url=settings.qdrant_url)


def create_collection() -> None:
    """
    Create the Qdrant collection if it does not exist.
    """

    if not client.collection_exists(settings.qdrant_collection):

        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE
            )
        )

        print("Qdrant collection created successfully!")

    else:
        print("Qdrant collection already exists.")


def store_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    document_id: str,
    filename: str
) -> list[str]:
    """
    Store document chunks and their embeddings in Qdrant.
    """

    if len(chunks) != len(embeddings):
        raise ValueError("Chunks and embeddings must have equal lengths.")

    if not chunks:
        return []

    points = []
    vector_ids = []

    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):

        vector_id = str(uuid4())
        vector_ids.append(vector_id)

        points.append(
            models.PointStruct(
                id=vector_id,
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": index,
                    "chunk_text": chunk
                }
            )
        )

    client.upsert(
        collection_name=settings.qdrant_collection,
        points=points,
        wait=True
    )

    return vector_ids


def search_similar_chunks(
    query_embedding: list[float],
    limit: int = 5
) -> list[dict]:

    """
    Find the most relevant document chunks.
    """

    results = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_embedding,
        limit=limit,
        with_payload=True
    )

    return [
        {
            "score": point.score,
            "payload": point.payload
        }
        for point in results.points
    ]

def delete_document_vectors(document_id: str) -> None:
    """
    Delete all vectors belonging to a document.
    """

    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id)
                    )
                ]
            )
        ),
        wait=True
    )
