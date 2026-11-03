# Document-Based Conversational RAG Backend

A document-based conversational Retrieval-Augmented Generation (RAG) backend built with FastAPI. It allows users to upload PDF and TXT documents, retrieve relevant information through semantic search, ask questions using a custom RAG pipeline, maintain multi-turn conversations, and book interviews through a conversational API.

## Features

- Upload PDF and TXT documents.
- Extract text from uploaded documents.
- Select between fixed-size and recursive chunking strategies.
- Generate local text embeddings using FastEmbed.
- Store document vectors in Qdrant.
- Store document metadata and interview bookings in SQLite.
- Retrieve relevant document chunks using semantic similarity search.
- Generate contextual answers using Google Gemini.
- Maintain multi-turn conversation history using Redis.
- Collect interview booking details conversationally.
- Request booking confirmation and persist confirmed bookings in SQLite.
- Automated tests for document parsing and chunking.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Vector Database | Qdrant |
| Metadata Database | SQLite, SQLAlchemy |
| Embedding Model | FastEmbed – BAAI/bge-small-en-v1.5 |
| Language Model | Google Gemini |
| Conversation Memory | Redis |
| Document Processing | PyMuPDF |
| Containerization | Docker Compose |
| Testing | Pytest |

## Project Structure

```text
rag_backend/
├── app/
│   ├── api/
│   │   ├── documents.py
│   │   ├── chat.py
│   │   └── booking.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── session.py
│   │   └── init_db.py
│   ├── services/
│   │   ├── document_parser.py
│   │   ├── chunking.py
│   │   ├── embedding.py
│   │   ├── vector_store.py
│   │   ├── llm.py
│   │   └── chat_memory.py
│   ├── main.py
│   └── models.py
├── tests/
│   ├── test_chunking.py
│   └── test_document_parser.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Prerequisites

Before running the application, install:

- Python 3.11 or later.
- Docker Desktop.
- A Google Gemini API key.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/joelgautam/document-rag-backend.git
cd rag_backend
```


### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it:

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a reference.

Add your Google Gemini API key and configure the required application settings.

For example:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model
```

Use the values and variable names specified in `.env.example`.

**Important:** Never commit your actual `.env` file or expose your API key publicly.

### 5. Start Qdrant and Redis

Make sure Docker Desktop is running, then execute:

```bash
docker compose up -d
```

This starts:

- Qdrant on port `6333`.
- Redis on port `6379`.

### 6. Start the FastAPI application

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

The API will be available at:

```text
http://127.0.0.1:8001
```

Open the interactive Swagger documentation:

[http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

## API Endpoints

### 1. Document Ingestion API

**Endpoint:** `POST /api/documents/upload`

Uploads a PDF or TXT document, extracts its text, splits the content into chunks, generates embeddings, and stores the vectors in Qdrant along with document metadata in SQLite.

**Request format:** `multipart/form-data`

Parameters:

| Parameter | Description |
|---|---|
| `file` | PDF or TXT document |
| `strategy` | `fixed` or `recursive` |

Example response:

```json
{
  "message": "Document uploaded and processed successfully.",
  "document_id": "generated-document-id",
  "filename": "sample.txt",
  "chunking_strategy": "recursive",
  "total_chunks": 1,
  "stored_vectors": 1,
  "metadata_saved": true
}
```

### 2. Conversational RAG API

**Endpoint:** `POST /api/chat/`

Accepts a user question, retrieves relevant document chunks through semantic similarity search, builds a custom RAG prompt, and generates a contextual answer using Google Gemini.

Conversation history is stored in Redis to support multi-turn conversations.

Example request:

```json
{
  "message": "What is Retrieval Augmented Generation?",
  "session_id": "conversation-001",
  "top_k": 5
}
```

Example response:

```json
{
  "session_id": "conversation-001",
  "answer": "Retrieval Augmented Generation combines document retrieval with language generation.",
  "sources": [
    {
      "filename": "sample.txt",
      "chunk_index": 0,
      "score": 0.6096
    }
  ]
}
```

The RAG pipeline is implemented manually without using a prebuilt `RetrievalQAChain`.

### 3. Interview Booking API

**Endpoint:** `POST /api/booking/`

Provides a conversational interview booking workflow.

The API collects:

- Candidate name.
- Email address.
- Interview date.
- Interview time.

The system checks for missing details, requests confirmation, and saves confirmed bookings in SQLite.

Redis is used to maintain the booking conversation state.

## Storage Design

| Storage | Purpose |
|---|---|
| Qdrant | Document embeddings, chunk text, and vector payloads |
| SQLite | Document chunk metadata and confirmed interview bookings |
| Redis | Conversation history and temporary booking state |

## Testing

Automated tests are implemented using Pytest.

Run the complete test suite:

```bash
python -m pytest -v
```

Current test coverage includes:

- Fixed-size chunking.
- Recursive chunking.
- Maximum chunk-size validation.
- Empty document handling.
- Invalid chunk size and overlap handling.
- Invalid chunking strategy handling.
- TXT document extraction.
- Unicode text extraction.
- PDF document extraction.
- Unsupported file extension handling.

**Latest test result: 12 passed.**

## Future Improvements

- Add API integration tests for ingestion, chat, and booking workflows.
- Improve date and time validation for interview bookings.
- Add authentication and authorization.
- Implement structured logging and monitoring.
- Add document deletion and management endpoints.
- Improve duplicate-upload handling and document version management.

## Author

**Joel Gautam**