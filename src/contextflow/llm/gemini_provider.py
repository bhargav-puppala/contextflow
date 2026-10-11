import os
from typing import Any

from dotenv import load_dotenv


class GeminiProvider:
    """LLMProvider implementation backed by the Gemini Interactions API."""

    def __init__(self, model: str = "gemini-3.6-flash", client: Any | None = None) -> None:
        load_dotenv()
        self._model = model
        self.last_usage: Any | None = None
        if client is not None:
            self._client = client
            return

        from google import genai

        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def generate(self, prompt: str) -> str:
        response = self._client.interactions.create(
            model=self._model,
            input=prompt,
        )
        self.last_usage = getattr(response, "usage", None)
        return response.output_text