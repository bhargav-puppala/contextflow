import pytest
from pydantic import ValidationError

from contextflow.models.task_state import Decision, FailedAttempt, TaskState


def test_task_state_accepts_structured_values() -> None:
    state = TaskState(
        objective="Build a weather application",
        constraints=["Use Python"],
        decisions=[Decision(decision="Use FastAPI", reason="Fits the backend")],
        completed_work=["Created the project structure"],
        current_state="Backend implementation is pending",
        failed_attempts=[
            FailedAttempt(
                approach="Node.js backend",
                result="Rejected",
                reason="The project requires Python",
            )
        ],
        artifacts=["src/contextflow/models/task_state.py"],
        pending_tasks=["Implement the API"],
        next_action="Create the API layer",
        metadata={"source": "agent-a"},
    )

    assert state.objective == "Build a weather application"
    assert state.decisions[0].reason == "Fits the backend"
    assert state.failed_attempts[0].approach == "Node.js backend"


def test_task_state_provides_independent_defaults() -> None:
    first = TaskState(objective="First task")
    second = TaskState(objective="Second task")

    assert first.constraints == []
    assert first.decisions == []
    assert first.completed_work == []
    assert first.current_state == ""
    assert first.failed_attempts == []
    assert first.artifacts == []
    assert first.pending_tasks == []
    assert first.next_action == ""
    assert first.metadata == {}

    first.constraints.append("Use Python")
    first.metadata["source"] = "test"
    assert second.constraints == []
    assert second.metadata == {}


def test_task_state_validates_field_types_and_required_values() -> None:
    with pytest.raises(ValidationError):
        TaskState(objective="Task", constraints=["valid", 123])

    with pytest.raises(ValidationError):
        TaskState(objective="Task", decisions=[{"reason": "Missing decision"}])

    with pytest.raises(ValidationError):
        TaskState(objective="")