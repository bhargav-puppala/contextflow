import os
from typing import Any


class OpenAIProvider:
    """LLMProvider implementation backed by the OpenAI Responses API."""

    def __init__(self, model: str = "gpt-4.1-mini", client: Any | None = None) -> None:
        self._model = model
        self.last_usage: Any | None = None
        if client is not None:
            self._client = client
            return

        from openai import OpenAI

        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def generate(self, prompt: str) -> str:
        response = self._client.responses.create(
            model=self._model,
            input=prompt,
        )
        self.last_usage = getattr(response, "usage", None)
        return response.output_text