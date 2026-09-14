from typing import Any, Mapping

from contextflow.models.task_state import TaskState


class TaskStateBuilder:
    """Build a validated task state from already-structured data."""

    @staticmethod
    def build(task_data: Mapping[str, Any]) -> TaskState:
        return TaskState.model_validate(task_data)