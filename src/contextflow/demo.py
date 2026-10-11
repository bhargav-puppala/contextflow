"""Run a deterministic, offline ContextFlow handoff demonstration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from contextflow.experiments import conversation_text, load_benchmark
from contextflow.handoff import build_continuation_prompt, build_handoff
from contextflow.metrics import count_tokens, token_reduction_percent
from contextflow.models.task_state import TaskState
from contextflow.storage import JsonTaskStore


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "demo" / "handoff.json"
DEFAULT_STORE = ROOT / "data" / "demo" / "tasks"


def offline_continuation(handoff: dict[str, Any]) -> str:
    """Create a deterministic continuation plan from handoff data only."""
    objective = handoff.get("objective", "the task")
    next_action = handoff.get("next_action", "Review the pending tasks")
    pending = handoff.get("pending_tasks", [])
    constraints = handoff.get("constraints", [])
    return (
        "Offline continuation (deterministic; not an LLM response)\n"
        f"Objective: {objective}\n"
        f"Next action: {next_action}\n"
        f"Pending tasks: {', '.join(pending) if pending else 'none listed'}\n"
        f"Constraints to preserve: {', '.join(constraints) if constraints else 'none listed'}"
    )


def run_demo(
    output_path: str | Path = DEFAULT_OUTPUT,
    store_dir: str | Path = DEFAULT_STORE,
) -> dict[str, Any]:
    """Load the representative fixture and demonstrate a local handoff."""
    benchmark = load_benchmark()
    conversation = conversation_text(benchmark)
    state = TaskState.model_validate(benchmark["expected_task_state"])
    handoff = build_handoff(benchmark["task_id"], state)

    store = JsonTaskStore(store_dir)
    task_path = Path(store_dir) / f"{benchmark['task_id']}.json"
    if task_path.exists():
        task_record = store.update(benchmark["task_id"], state)
    else:
        task_record = store.create(benchmark["task_id"], state)

    handoff_path = Path(output_path)
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(
        json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    fresh_record = JsonTaskStore(store_dir).get(benchmark["task_id"])
    fresh_state = TaskState.model_validate(fresh_record["state"])
    fresh_handoff = build_handoff(benchmark["task_id"], fresh_state)
    continuation_prompt = build_continuation_prompt(fresh_handoff)

    original_tokens = count_tokens(conversation)
    handoff_tokens = count_tokens(
        json.dumps(fresh_handoff, separators=(",", ":"), sort_keys=True)
    )
    return {
        "demo": "offline_contextflow_handoff",
        "extraction_mode": "deterministic_expected_task_state_fixture",
        "source_fixture": "src/contextflow/data/experiment_001.json",
        "original_conversation": conversation,
        "objective": fresh_state.objective,
        "task_state": fresh_state.model_dump(mode="json"),
        "handoff_path": str(handoff_path),
        "task_record": {
            "task_id": task_record["task_id"],
            "version": task_record["version"],
            "store_dir": str(store_dir),
        },
        "token_estimates": {
            "method": "contextflow.metrics.count_tokens using cl100k_base",
            "original_conversation": original_tokens,
            "handoff": handoff_tokens,
            "reduction_percent": token_reduction_percent(original_tokens, handoff_tokens),
        },
        "fresh_session": {
            "loaded_from_store": True,
            "original_conversation_provided": False,
            "continuation_prompt": continuation_prompt,
            "continuation_response": offline_continuation(fresh_handoff),
        },
    }