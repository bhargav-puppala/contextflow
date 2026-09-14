from contextflow.engine.extractor import ContextExtractor
from contextflow.engine.mock_extractor import MockContextExtractor
from contextflow.engine.state_builder import TaskStateBuilder


def test_mock_extractor_output_builds_valid_task_state() -> None:
    extractor: ContextExtractor = MockContextExtractor()

    structured_data = extractor.extract(
        "The user wants a deterministic development implementation."
    )
    state = TaskStateBuilder.build(structured_data)

    assert state.objective == "Demonstrate deterministic context extraction"
    assert state.current_state == "Using the mock extractor"
    assert state.metadata == {"extractor": "mock"}


def test_mock_extractor_handles_empty_input_deterministically() -> None:
    extractor = MockContextExtractor()

    first_state = TaskStateBuilder.build(extractor.extract(""))
    second_state = TaskStateBuilder.build(extractor.extract(" "))

    assert first_state == second_state