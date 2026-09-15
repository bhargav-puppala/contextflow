import json
from typing import Any, Mapping

from contextflow.engine.prioritizer import ContextPrioritizer
from contextflow.models.task_state import TaskState


def build_handoff(
    task_id: str,
    task_state: TaskState,
    version: int = 1,
) -> dict[str, Any]:
    """Build a compact machine-readable package for a receiving agent."""
    selected = ContextPrioritizer().prioritize(task_state)
    context = {
        key: value
        for key, value in selected.items()
        if value not in ("", [], {})
    }
    if task_state.artifacts:
        context["artifacts"] = task_state.artifacts
    return {"task_id": task_id, "version": version, **context}


def build_continuation_prompt(handoff: Mapping[str, Any]) -> str:
    """Turn a handoff package into instructions for Agent B."""
    if not isinstance(handoff, Mapping):
        raise TypeError("handoff must be a mapping")

    serialized = json.dumps(handoff, separators=(",", ":"), sort_keys=True)
    return (
        "Continue the task from the supplied handoff state. Do not redo completed "
        "work. Respect all constraints. Use failed attempts to avoid repeating "
        "mistakes. Determine the next appropriate action and continue the task.\n\n"
        "Handoff state:\n"
        f"{serialized}"
    )