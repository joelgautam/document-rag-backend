
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.embedding import generate_embedding
from app.services.vector_store import search_similar_chunks
from app.services.chat_memory import (
    get_chat_history,
    save_chat_message
)
from app.services.llm import generate_answer


router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=10)


@router.post("/")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        # 1. Create or reuse conversation session
        session_id = request.session_id or str(uuid4())

        # 2. Retrieve previous conversation
        history = get_chat_history(session_id)

        # 3. Convert user question into an embedding
        query_embedding = generate_embedding(request.message)

        # 4. Search Qdrant for relevant document chunks
        retrieved_chunks = search_similar_chunks(
            query_embedding=query_embedding,
            limit=request.top_k
        )

        # 5. Prepare document context
        context = "\n\n".join(
            [
                item["payload"]["chunk_text"]
                for item in retrieved_chunks
                if item.get("payload")
                and item["payload"].get("chunk_text")
            ]
        )

        if not context:
            context = (
                "No relevant information was found in the uploaded documents."
            )

        # 6. Prepare conversation history
        conversation_history = "\n".join(
            [
                f'{message["role"]}: {message["content"]}'
                for message in history[-10:]
            ]
        )

        # 7. Build the RAG prompt
        prompt = f"""
You are a helpful document question-answering assistant.

Answer the user's question using the provided document context.

If the answer is not available in the document context,
clearly say that the uploaded documents do not contain
enough information.

Do not invent facts.

DOCUMENT CONTEXT:
{context}

PREVIOUS CONVERSATION:
{conversation_history}

CURRENT USER QUESTION:
{request.message}

Provide a clear and helpful answer.
"""

        # 8. Generate answer using Gemini
        answer = generate_answer(prompt)

        # 9. Save both messages in Redis
        save_chat_message(
            session_id,
            "user",
            request.message
        )

        save_chat_message(
            session_id,
            "assistant",
            answer
        )

        # 10. Return answer and source information
        sources = [
            {
                "filename": item["payload"].get("filename"),
                "chunk_index": item["payload"].get("chunk_index"),
                "score": item.get("score")
            }
            for item in retrieved_chunks
            if item.get("payload")
        ]

        return {
            "session_id": session_id,
            "answer": answer,
            "sources": sources
        }

    except Exception as error:
        error_message = str(error)

        # Handle temporary Gemini service or rate-limit errors
        if (
            "503" in error_message
            or "UNAVAILABLE" in error_message
            or "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
        ):
            raise HTTPException(
                status_code=503,
                detail=(
                    "Gemini is temporarily unavailable. "
                    "Please try again shortly."
                )
            ) from error

        # Handle other unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(error)}"
        ) from error
