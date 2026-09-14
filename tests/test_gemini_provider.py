from types import SimpleNamespace

import pytest

from contextflow.llm.gemini_provider import GeminiProvider


class FakeModels:
    def __init__(self, response: object = SimpleNamespace(text="generated text")) -> None:
        self.response = response
        self.calls: list[dict[str, str]] = []

    def generate_content(self, **kwargs: str) -> object:
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, models: FakeModels) -> None:
        self.models = models


def test_gemini_provider_returns_generated_text() -> None:
    models = FakeModels()
    provider = GeminiProvider(model="test-model", client=FakeClient(models))

    result = provider.generate("Summarize this task")

    assert result == "generated text"
    assert models.calls == [
        {"model": "test-model", "contents": "Summarize this task"}
    ]


def test_gemini_provider_propagates_client_errors() -> None:
    class FailingModels:
        def generate_content(self, **kwargs: str) -> object:
            raise RuntimeError("client failure")

    provider = GeminiProvider(client=FakeClient(FailingModels()))

    with pytest.raises(RuntimeError, match="client failure"):
        provider.generate("Any prompt")