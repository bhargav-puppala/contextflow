import os
from typing import Any


class GeminiProvider:
    """LLMProvider implementation backed by the Gemini API."""

    def __init__(self, model: str = "gemini-2.5-flash", client: Any | None = None) -> None:
        self._model = model
        if client is not None:
            self._client = client
            return

        from google import genai

        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return response.text