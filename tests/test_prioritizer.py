import pytest

from contextflow.engine.prioritizer import ContextPrioritizer
from contextflow.models.task_state import Decision, FailedAttempt, TaskState


def test_prioritizer_preserves_required_task_state_information() -> None:
    task_state = TaskState(
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
        artifacts=["README.md"],
        pending_tasks=["Implement authentication"],
        next_action="Create the authentication endpoint",
        metadata={"source": "agent-a"},
    )

    transferable = ContextPrioritizer().prioritize(task_state)

    assert transferable == {
        "objective": "Build a weather application",
        "constraints": ["Use Python"],
        "decisions": [
            {"decision": "Use FastAPI", "reason": "Fits the backend"}
        ],
        "completed_work": ["Created the project structure"],
        "current_state": "Backend implementation is pending",
        "failed_attempts": [
            {
                "approach": "Node.js backend",
                "result": "Rejected",
                "reason": "The project requires Python",
            }
        ],
        "pending_tasks": ["Implement authentication"],
        "next_action": "Create the authentication endpoint",
    }


def test_prioritizer_requires_a_task_state() -> None:
    with pytest.raises(TypeError, match="must be a TaskState"):
        ContextPrioritizer().prioritize({"objective": "Build an app"})