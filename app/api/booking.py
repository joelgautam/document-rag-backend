
import json
import re
from uuid import uuid4
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import InterviewBooking
from app.services.chat_memory import redis_client
from app.services.llm import generate_answer


router = APIRouter(prefix="/api/booking", tags=["Interview Booking"])

BOOKING_TTL = 86400


class BookingRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None


def get_booking_draft(session_id: str) -> dict:
    """Retrieve incomplete booking details from Redis."""

    data = redis_client.get(f"booking:{session_id}")

    if data:
        return json.loads(data)

    return {}


def save_booking_draft(session_id: str, draft: dict) -> None:
    """Temporarily save booking details in Redis."""

    redis_client.set(
        f"booking:{session_id}",
        json.dumps(draft),
        ex=BOOKING_TTL
    )


def extract_booking_details(message: str) -> dict:
    """Use Gemini to interpret natural-language booking details."""

    prompt = f"""
Extract interview booking information from the candidate's message.

Today's date is {date.today().isoformat()}.

Return ONLY a valid JSON object with these four keys:
candidate_name, email, interview_date, interview_time.

Rules:
- Extract only information explicitly provided by the candidate.
- Use null for any missing information.
- Format dates as YYYY-MM-DD when unambiguous.
- Format times as HH:MM in 24-hour format when unambiguous.
- Do not invent or guess missing details.
- Do not include Markdown or explanations.

Candidate message:
{message}
"""

    response = generate_answer(prompt)

    cleaned = response.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "")

    details = json.loads(cleaned)

    required_keys = [
        "candidate_name",
        "email",
        "interview_date",
        "interview_time"
    ]

    return {
        field: details.get(field)
        for field in required_keys
    }


def extract_local_booking_details(message: str) -> dict:
    """Extract common booking details without calling Gemini."""

    details = {
        "candidate_name": None,
        "email": None,
        "interview_date": None,
        "interview_time": None
    }

    # Extract candidate name
    name_match = re.search(
        r"\b(?:my name is|i am|i'm|name is|name:)\s*"
        r"([A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,4})",
        message,
        re.IGNORECASE
    )

    if name_match:
        details["candidate_name"] = name_match.group(1).strip()

    # Extract email
    email_match = re.search(
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        message
    )

    if email_match:
        details["email"] = email_match.group(0)

    # Extract date in YYYY-MM-DD format
    date_match = re.search(
        r"\b\d{4}-\d{2}-\d{2}\b",
        message
    )

    if date_match:
        details["interview_date"] = date_match.group(0)

    # Extract time in 24-hour HH:MM format
    time_match = re.search(
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        message
    )

    if time_match:
        details["interview_time"] = (
            f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
        )

    return details


def get_missing_fields(draft: dict) -> list[str]:
    """Identify booking details that have not been provided."""

    required_fields = [
        "candidate_name",
        "email",
        "interview_date",
        "interview_time"
    ]

    return [
        field for field in required_fields
        if not draft.get(field)
    ]


@router.post("/")
def book_interview(
    request: BookingRequest,
    db: Session = Depends(get_db)
):
    try:
        session_id = request.session_id or str(uuid4())

        message = request.message.strip()
        key = f"booking:{session_id}"

        draft = get_booking_draft(session_id)

        # 1. Handle cancellation
        if message.lower() in [
            "cancel",
            "cancel booking",
            "start over"
        ]:
            redis_client.delete(key)

            return {
                "session_id": session_id,
                "status": "cancelled",
                "message": "Your booking draft has been cancelled."
            }

        # 2. Handle candidate confirmation
        if draft.get("awaiting_confirmation"):

            if message.lower() in [
                "yes",
                "confirm",
                "confirmed",
                "correct"
            ]:
                booking = InterviewBooking(
                    candidate_name=draft["candidate_name"],
                    email=draft["email"],
                    interview_date=draft["interview_date"],
                    interview_time=draft["interview_time"],
                    status="confirmed"
                )

                db.add(booking)
                db.commit()
                db.refresh(booking)

                redis_client.delete(key)

                return {
                    "session_id": session_id,
                    "status": "confirmed",
                    "booking_id": booking.id,
                    "message": "Your interview has been booked successfully.",
                    "booking": {
                        "candidate_name": booking.candidate_name,
                        "email": booking.email,
                        "interview_date": booking.interview_date,
                        "interview_time": booking.interview_time
                    }
                }

            if message.lower() in [
                "no",
                "not correct",
                "change"
            ]:
                draft.pop("awaiting_confirmation", None)
                save_booking_draft(session_id, draft)

                return {
                    "session_id": session_id,
                    "status": "collecting",
                    "message": (
                        "No problem. Please provide the corrected "
                        "booking details."
                    )
                }

            return {
                "session_id": session_id,
                "status": "awaiting_confirmation",
                "message": "Please reply YES to confirm or NO to change your booking."
            }

        # 3. Extract details locally first
        extracted = extract_local_booking_details(message)

        # 4. Use Gemini only if local extraction finds no details
        if not any(extracted.values()):
            try:
                extracted = extract_booking_details(message)
            except Exception:
                # Continue collecting details even if Gemini is unavailable
                extracted = {}

        # 5. Merge new details with existing booking draft
        for field in [
            "candidate_name",
            "email",
            "interview_date",
            "interview_time"
        ]:
            value = extracted.get(field)

            if value:
                draft[field] = str(value).strip()

        # 6. Validate email
        email = draft.get("email")

        if email and not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email
        ):
            return {
                "session_id": session_id,
                "status": "collecting",
                "message": (
                    "That email address does not look valid. "
                    "Please provide a valid email."
                )
            }

        # 7. Validate date
        interview_date = draft.get("interview_date")

        if interview_date:
            try:
                parsed_date = date.fromisoformat(interview_date)

                if parsed_date < date.today():
                    draft.pop("interview_date", None)
                    save_booking_draft(session_id, draft)

                    return {
                        "session_id": session_id,
                        "status": "collecting",
                        "message": (
                            "That date is in the past. "
                            "Please provide a future interview date."
                        )
                    }

            except ValueError:
                draft.pop("interview_date", None)

        # 8. Validate time
        interview_time = draft.get("interview_time")

        if interview_time:
            try:
                datetime.strptime(interview_time, "%H:%M")
            except ValueError:
                draft.pop("interview_time", None)

        # 9. Check for missing details
        missing = get_missing_fields(draft)

        if missing:
            save_booking_draft(session_id, draft)

            questions = {
                "candidate_name": "What is your full name?",
                "email": "What is your email address?",
                "interview_date": (
                    "What date would you prefer? "
                    "Please use YYYY-MM-DD."
                ),
                "interview_time": (
                    "What time would you prefer? "
                    "Please use 24-hour format, such as 14:30."
                )
            }

            next_field = missing[0]

            return {
                "session_id": session_id,
                "status": "collecting",
                "message": questions[next_field],
                "missing_fields": missing
            }

        # 10. Ask candidate to confirm all details
        draft["awaiting_confirmation"] = True

        save_booking_draft(session_id, draft)

        return {
            "session_id": session_id,
            "status": "awaiting_confirmation",
            "message": (
                "Please confirm your interview booking details "
                "by replying YES:\n"
                f"Name: {draft['candidate_name']}\n"
                f"Email: {draft['email']}\n"
                f"Date: {draft['interview_date']}\n"
                f"Time: {draft['interview_time']}"
            )
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Booking processing failed: {str(error)}"
        ) from error
