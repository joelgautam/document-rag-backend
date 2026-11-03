
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.session import get_db
from app.models import DocumentChunk

from app.services.document_parser import extract_document_text
from app.services.chunking import chunk_document
from app.services.embedding import generate_embeddings
from app.services.vector_store import (
    create_collection,
    store_chunks,
    delete_document_vectors
)


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    strategy: str = Form("recursive"),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF or TXT document, split it into chunks,
    generate embeddings, and store the results.
    """

    # 1. Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )

    extension = file.filename.lower().rsplit(".", 1)[-1]

    if extension not in ["pdf", "txt"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported."
        )

    # 2. Validate chunking strategy
    if strategy not in ["fixed", "recursive"]:
        raise HTTPException(
            status_code=400,
            detail="Strategy must be 'fixed' or 'recursive'."
        )

    # 3. Read uploaded file
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    # 4. Extract document text
    try:
        extracted_text = extract_document_text(
            file.filename,
            file_bytes
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Document extraction failed: {error}"
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the document."
        )

    # 5. Split document into chunks
    try:
        chunks = chunk_document(
            extracted_text,
            strategy=strategy
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No chunks could be generated."
        )

    # 6. Generate embeddings
    try:
        embeddings = generate_embeddings(chunks)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Embedding generation failed: {error}"
        )

    # 7. Generate a unique document ID
    document_id = str(uuid4())

    # 8. Store vectors and metadata
    vector_ids = []

    try:
        create_collection()

        vector_ids = store_chunks(
            chunks=chunks,
            embeddings=embeddings,
            document_id=document_id,
            filename=file.filename
        )

        for index, (chunk, vector_id) in enumerate(
            zip(chunks, vector_ids)
        ):
            db_chunk = DocumentChunk(
                document_id=document_id,
                filename=file.filename,
                chunk_index=index,
                chunk_text=chunk,
                vector_id=vector_id
            )

            db.add(db_chunk)

        db.commit()

    except Exception as error:
        db.rollback()

        if vector_ids:
            try:
                delete_document_vectors(document_id)
            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail=f"Document storage failed: {error}"
        )

    # 9. Return upload result
    return {
        "message": "Document uploaded and processed successfully.",
        "document_id": document_id,
        "filename": file.filename,
        "chunking_strategy": strategy,
        "total_chunks": len(chunks),
        "stored_vectors": len(vector_ids),
        "metadata_saved": True
    }
