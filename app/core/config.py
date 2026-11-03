from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # OpenAI configuration
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    # Qdrant configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "documents"

    # Redis configuration
    redis_url: str = "redis://localhost:6379/0"

    # SQL database configuration
    database_url: str = "sqlite:///./rag_backend.db"

    # Document chunking configuration
    chunk_size: int = 800
    chunk_overlap: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()