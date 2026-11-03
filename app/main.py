
from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.booking import router as booking_router

app = FastAPI(
    title="Document RAG Backend",
    description=(
        "A document ingestion and conversational "
        "Retrieval-Augmented Generation backend."
    ),
    version="1.0.0"
)


# Register document ingestion routes
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(booking_router)



@app.get("/")
def home():
    return {
        "message": "Document RAG Backend is running!",
        "status": "healthy"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
