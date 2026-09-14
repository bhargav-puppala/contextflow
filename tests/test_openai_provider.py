from types import SimpleNamespace

import pytest

from contextflow.llm.openai_provider import OpenAIProvider


class FakeResponses:
    def __init__(self, response: object = SimpleNamespace(output_text="generated text")) -> None:
        self.response = response
        self.calls: list[dict[str, str]] = []

    def create(self, **kwargs: str) -> object:
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, responses: FakeResponses) -> None:
        self.responses = responses


def test_openai_provider_returns_responses_api_text() -> None:
    responses = FakeResponses()
    provider = OpenAIProvider(model="test-model", client=FakeClient(responses))

    result = provider.generate("Summarize this task")

    assert result == "generated text"
    assert responses.calls == [
        {"model": "test-model", "input": "Summarize this task"}
    ]


def test_openai_provider_propagates_client_errors() -> None:
    class FailingResponses:
        def create(self, **kwargs: str) -> object:
            raise RuntimeError("client failure")

    provider = OpenAIProvider(client=FakeClient(FailingResponses()))

    with pytest.raises(RuntimeError, match="client failure"):
        provider.generate("Any prompt")