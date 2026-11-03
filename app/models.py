from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    document_id: Mapped[str] = mapped_column(String(100), index=True)

    filename: Mapped[str] = mapped_column(String(255))

    chunk_index: Mapped[int] = mapped_column(Integer)

    chunk_text: Mapped[str] = mapped_column(Text)

    vector_id: Mapped[str] = mapped_column(String(100), unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class InterviewBooking(Base):
    __tablename__ = "interview_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    candidate_name: Mapped[str] = mapped_column(String(150))

    email: Mapped[str] = mapped_column(String(255))

    interview_date: Mapped[str] = mapped_column(String(50))

    interview_time: Mapped[str] = mapped_column(String(50))

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )