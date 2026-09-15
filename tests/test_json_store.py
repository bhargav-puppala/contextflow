import pytest

from contextflow.models.task_state import TaskState
from contextflow.storage import JsonTaskStore


def test_json_store_creates_retrieves_and_versions_tasks(tmp_path) -> None:
    store = JsonTaskStore(tmp_path)
    initial = TaskState(objective="Build an API", pending_tasks=["Add tests"])
    updated = TaskState(objective="Build an API", pending_tasks=["Run tests"])

    created = store.create("task-001", initial)
    changed = store.update("task-001", updated)

    assert created["version"] == 1
    assert changed["version"] == 2
    assert changed["history"][0]["state"]["pending_tasks"] == ["Add tests"]
    assert store.get("task-001")["state"]["pending_tasks"] == ["Run tests"]
    assert store.list_tasks() == ["task-001"]


def test_json_store_rejects_duplicate_and_missing_tasks(tmp_path) -> None:
    store = JsonTaskStore(tmp_path)
    state = TaskState(objective="Build an API")

    store.create("task-001", state)
    with pytest.raises(FileExistsError):
        store.create("task-001", state)
    with pytest.raises(FileNotFoundError):
        store.get("missing")