import pytest

from contextflow.engine.context_engine import ContextEngine
from contextflow.engine.llm_extractor import LLMContextExtractor


class FakeLLMProvider:
    def __init__(self, response: str) -> None:
        self.response = response

    def generate(self, prompt: str) -> str:
        return self.response


class FailingExtractor:
    def extract(self, context: str) -> dict[str, str]:
        raise RuntimeError("extraction failed")


def test_context_engine_runs_the_complete_pipeline() -> None:
    extractor = LLMContextExtractor(
        FakeLLMProvider(
            '{"objective":"Build an app",'
            '"constraints":["Use Python"],'
            '"current_state":"API is pending",'
            '"pending_tasks":["Implement API"],'
            '"next_action":"Create the endpoint"}'
        )
    )

    result = ContextEngine(extractor).process("Build an app with Python.")

    assert result == (
        '{"completed_work":[],"constraints":["Use Python"],'
        '"current_state":"API is pending","decisions":[],'
        '"failed_attempts":[],"next_action":"Create the endpoint",'
        '"objective":"Build an app","pending_tasks":["Implement API"]}'
    )


def test_context_engine_propagates_extractor_errors() -> None:
    engine = ContextEngine(FailingExtractor())

    with pytest.raises(RuntimeError, match="extraction failed"):
        engine.process("Any conversation")