from typing import Any

from contextflow.engine.extractor import ContextExtractor
from contextflow.engine.state_builder import TaskStateBuilder


class StubExtractor:
    def extract(self, context: str | dict[str, Any]) -> dict[str, Any]:
        assert context
        return {
            "objective": "Build a weather application",
            "decisions": [{"decision": "Use FastAPI"}],
        }


def test_extractor_protocol_accepts_provider_neutral_implementation() -> None:
    extractor: ContextExtractor = StubExtractor()

    structured_data = extractor.extract("The user wants a weather application.")
    state = TaskStateBuilder.build(structured_data)

    assert state.objective == "Build a weather application"
    assert state.decisions[0].decision == "Use FastAPI"


def test_extractor_contract_accepts_structured_context() -> None:
    extractor: ContextExtractor = StubExtractor()

    structured_data = extractor.extract({"conversation": "Build the application"})

    assert structured_data["objective"] == "Build a weather application"