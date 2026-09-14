from types import SimpleNamespace

import pytest

from contextflow.llm.gemini_provider import GeminiProvider


class FakeInteractions:
    def __init__(self, response: object = SimpleNamespace(output_text="generated text")) -> None:
        self.response = response
        self.calls: list[dict[str, str]] = []

    def create(self, **kwargs: str) -> object:
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, interactions: FakeInteractions) -> None:
        self.interactions = interactions


def test_gemini_provider_returns_generated_text() -> None:
    interactions = FakeInteractions()
    provider = GeminiProvider(model="test-model", client=FakeClient(interactions))

    result = provider.generate("Summarize this task")

    assert result == "generated text"
    assert interactions.calls == [
        {"model": "test-model", "input": "Summarize this task"}
    ]


def test_gemini_provider_propagates_client_errors() -> None:
    class FailingInteractions:
        def create(self, **kwargs: str) -> object:
            raise RuntimeError("client failure")

    provider = GeminiProvider(client=FakeClient(FailingInteractions()))

    with pytest.raises(RuntimeError, match="client failure"):
        provider.generate("Any prompt")