import pytest

from contextflow.handoff import build_continuation_prompt, build_handoff
from contextflow.models.task_state import Decision, FailedAttempt, TaskState


def test_handoff_contains_transferable_state_and_identity() -> None:
    state = TaskState(
        objective="Build an API",
        constraints=["Keep the schema"],
        decisions=[Decision(decision="Use FastAPI", reason="Python fit")],
        completed_work=["Created models"],
        current_state="Authentication is pending",
        failed_attempts=[
            FailedAttempt(approach="SQLite", result="Abandoned", reason="PostgreSQL required")
        ],
        artifacts=["src/app.py"],
        pending_tasks=["Add JWT"],
        next_action="Investigate the auth error",
        metadata={"source": "agent-a"},
    )

    handoff = build_handoff("task-001", state, version=3)

    assert handoff["task_id"] == "task-001"
    assert handoff["version"] == 3
    assert handoff["decisions"][0]["reason"] == "Python fit"
    assert handoff["artifacts"] == ["src/app.py"]
    assert "metadata" not in handoff


def test_continuation_prompt_contains_agent_b_instructions() -> None:
    prompt = build_continuation_prompt({"task_id": "task-001", "objective": "Build an API"})

    assert "Do not redo completed work" in prompt
    assert "Respect all constraints" in prompt
    assert "failed attempts" in prompt
    assert '"task_id":"task-001"' in prompt


def test_continuation_prompt_rejects_non_mapping() -> None:
    with pytest.raises(TypeError):
        build_continuation_prompt([])