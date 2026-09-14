import pytest
from pydantic import ValidationError

from contextflow.engine.state_builder import TaskStateBuilder


def test_builder_constructs_task_state_from_structured_data() -> None:
    state = TaskStateBuilder.build(
        {
            "objective": "Build a weather application",
            "constraints": ["Use Python"],
            "decisions": [
                {"decision": "Use FastAPI", "reason": "Fits the backend"}
            ],
            "failed_attempts": [
                {
                    "approach": "Node.js backend",
                    "result": "Rejected",
                    "reason": "The project requires Python",
                }
            ],
            "pending_tasks": ["Implement authentication"],
        }
    )

    assert state.objective == "Build a weather application"
    assert state.decisions[0].decision == "Use FastAPI"
    assert state.failed_attempts[0].result == "Rejected"
    assert state.pending_tasks == ["Implement authentication"]


def test_builder_rejects_invalid_structured_data() -> None:
    with pytest.raises(ValidationError):
        TaskStateBuilder.build(
            {
                "objective": "Build a weather application",
                "decisions": [{"reason": "The decision is missing"}],
            }
        )