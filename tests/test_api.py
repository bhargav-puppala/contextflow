from contextflow.api import ContextFlow
from contextflow.storage import JsonTaskStore


def test_contextflow_api_persists_updates_and_builds_handoff(tmp_path) -> None:
    flow = ContextFlow(store=JsonTaskStore(tmp_path))

    created = flow.create_task("task-001", "Build an application")
    updated = flow.update_task("task-001", "Finish the application")
    handoff = flow.handoff("task-001")

    assert created["version"] == 1
    assert updated["version"] == 2
    assert flow.get_task("task-001")["version"] == 2
    assert handoff["task_id"] == "task-001"
    assert handoff["version"] == 2
    assert "Continue the task" in flow.continuation_prompt("task-001")


def test_contextflow_default_process_uses_existing_mock_pipeline(tmp_path) -> None:
    flow = ContextFlow(store=JsonTaskStore(tmp_path))

    result = flow.process("Any conversation")

    assert '"objective":"Demonstrate deterministic context extraction"' in result