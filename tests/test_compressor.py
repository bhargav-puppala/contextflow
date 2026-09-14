import pytest

from contextflow.engine.compressor import serialize_context
from contextflow.engine.prioritizer import ContextPrioritizer
from contextflow.models.task_state import TaskState


def test_serialize_context_produces_compact_json() -> None:
    task_state = TaskState(
        objective="Build a weather application",
        constraints=["Use Python"],
        current_state="Backend is pending",
        pending_tasks=["Implement the API"],
        next_action="Create the API endpoint",
    )
    transferable = ContextPrioritizer().prioritize(task_state)

    serialized = serialize_context(transferable)

    assert serialized == (
        '{"completed_work":[],"constraints":["Use Python"],'
        '"current_state":"Backend is pending","decisions":[],'
        '"failed_attempts":[],"next_action":"Create the API endpoint",'
        '"objective":"Build a weather application",'
        '"pending_tasks":["Implement the API"]}'
    )


def test_serialize_context_is_deterministic() -> None:
    context = {"objective": "Build an app", "constraints": ["Use Python"]}

    assert serialize_context(context) == serialize_context(context)


def test_serialize_context_rejects_invalid_input() -> None:
    with pytest.raises(TypeError, match="must be a mapping"):
        serialize_context([("objective", "Build an app")])