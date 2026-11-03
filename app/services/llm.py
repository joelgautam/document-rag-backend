
import os
import time

from dotenv import load_dotenv
from google import genai


# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from the .env file.")

client = genai.Client(api_key=API_KEY)


def generate_answer(prompt: str) -> str:
    """
    Send a prompt to Gemini and retry temporary failures.
    """

    if not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            if not response.text:
                raise RuntimeError("Gemini returned an empty response.")

            return response.text.strip()

        except Exception as error:
            error_message = str(error)

            is_temporary_error = (
                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            )

            if not is_temporary_error or attempt == 2:
                raise

            time.sleep(2 ** attempt)

    raise RuntimeError("Gemini could not generate an answer.")
