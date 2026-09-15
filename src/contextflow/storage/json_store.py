import json
from pathlib import Path
from typing import Any

from contextflow.models.task_state import TaskState


class JsonTaskStore:
    """Small local JSON store with replacement updates and version history."""

    def __init__(self, root: str | Path = "data/tasks") -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def create(self, task_id: str, task_state: TaskState) -> dict[str, Any]:
        path = self._path(task_id)
        if path.exists():
            raise FileExistsError(f"Task already exists: {task_id}")
        return self._write(task_id, task_state, version=1, history=[])

    def update(self, task_id: str, task_state: TaskState) -> dict[str, Any]:
        record = self.get(task_id)
        history = record.get("history", [])
        history.append({"version": record["version"], "state": record["state"]})
        return self._write(
            task_id,
            task_state,
            version=record["version"] + 1,
            history=history,
        )

    def get(self, task_id: str) -> dict[str, Any]:
        path = self._path(task_id)
        if not path.exists():
            raise FileNotFoundError(f"Task not found: {task_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def list_tasks(self) -> list[str]:
        return sorted(path.stem for path in self._root.glob("*.json"))

    def _path(self, task_id: str) -> Path:
        if not task_id or Path(task_id).name != task_id:
            raise ValueError("task_id must be a non-empty filename-safe value")
        return self._root / f"{task_id}.json"

    def _write(
        self,
        task_id: str,
        task_state: TaskState,
        version: int,
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        record = {
            "task_id": task_id,
            "version": version,
            "state": task_state.model_dump(mode="json"),
            "history": history,
        }
        self._path(task_id).write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return record