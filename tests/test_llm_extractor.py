import pytest
from pydantic import ValidationError

from contextflow.engine.llm_extractor import LLMContextExtractor
from contextflow.models.task_state import TaskState


class FakeLLMProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def test_valid_json_response_becomes_task_state_and_includes_conversation() -> None:
    provider = FakeLLMProvider(
        '{"objective": "Build a weather app", "pending_tasks": ["Add tests"]}'
    )
    extractor = LLMContextExtractor(provider)

    state = extractor.extract("The user wants a weather app.")

    assert isinstance(state, TaskState)
    assert state.objective == "Build a weather app"
    assert state.pending_tasks == ["Add tests"]
    assert len(provider.prompts) == 1
    assert "The user wants a weather app." in provider.prompts[0]


def test_fenced_json_response_becomes_task_state() -> None:
    provider = FakeLLMProvider(
        '```json\n{"objective": "Build a weather app"}\n```'
    )
    extractor = LLMContextExtractor(provider)

    state = extractor.extract("The user wants a weather app.")

    assert state.objective == "Build a weather app"


def test_invalid_json_is_handled_cleanly() -> None:
    extractor = LLMContextExtractor(FakeLLMProvider("not json"))

    with pytest.raises(ValueError, match="invalid JSON"):
        extractor.extract("Some conversation")


def test_invalid_task_state_data_is_rejected() -> None:
    provider = FakeLLMProvider('{"decisions": [{"reason": "Missing decision"}]}')
    extractor = LLMContextExtractor(provider)

    with pytest.raises(ValidationError):
        extractor.extract("Some conversation")