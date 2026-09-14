from typing import Any

from contextflow.models.task_state import TaskState


TRANSFERABLE_FIELDS = (
    "objective",
    "constraints",
    "decisions",
    "completed_work",
    "current_state",
    "failed_attempts",
    "pending_tasks",
    "next_action",
)


class ContextPrioritizer:
    """Select the deterministic minimum task context for transfer."""

    def prioritize(self, task_state: TaskState) -> dict[str, Any]:
        if not isinstance(task_state, TaskState):
            raise TypeError("task_state must be a TaskState")

        return task_state.model_dump(include=set(TRANSFERABLE_FIELDS))