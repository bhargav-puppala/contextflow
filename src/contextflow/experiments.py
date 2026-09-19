import json
from importlib import resources
from pathlib import Path
from typing import Any

from contextflow.handoff import build_continuation_prompt, build_handoff
from contextflow.llm import LLMProvider
from contextflow.metrics import count_tokens, token_reduction_percent
from contextflow.models.task_state import TaskState


DEFAULT_BENCHMARK = resources.files("contextflow").joinpath(
    "data", "experiment_001.json"
)


def load_benchmark(path: str | Path = DEFAULT_BENCHMARK) -> dict[str, Any]:
    resource = Path(path) if isinstance(path, (str, Path)) else path
    contents = resource.read_text(encoding="utf-8")
    return json.loads(contents)


def conversation_text(benchmark: dict[str, Any]) -> str:
    return "\n".join(
        f"{message['role']}: {message['content']}"
        for message in benchmark["agent_a_conversation"]
    )


def run_benchmark(
    path: str | Path = DEFAULT_BENCHMARK,
    summary_provider: LLMProvider | None = None,
) -> dict[str, Any]:
    """Run the offline benchmark using its deterministic gold task-state fixture."""
    benchmark = load_benchmark(path)
    original = conversation_text(benchmark)
    state = TaskState.model_validate(benchmark["expected_task_state"])
    handoff = build_handoff(benchmark["task_id"], state)
    handoff_json = json.dumps(handoff, separators=(",", ":"), sort_keys=True)
    continuation = build_continuation_prompt(handoff)
    original_tokens = count_tokens(original)

    conditions = {
        "full_conversation": {
            "context": original,
            "tokens": original_tokens,
        },
        "contextflow_structured_handoff": {
            "context": handoff_json,
            "tokens": count_tokens(handoff_json),
            "continuation_prompt": continuation,
            "continuation_prompt_tokens": count_tokens(continuation),
        },
    }
    if summary_provider is not None:
        summary = summary_provider.generate(
            "Summarize this software-development conversation for a receiving agent.\n\n"
            f"{original}"
        )
        conditions["llm_summary"] = {
            "context": summary,
            "tokens": count_tokens(summary),
            "continuation_prompt": summary,
            "continuation_prompt_tokens": count_tokens(summary),
        }
    transferred_tokens = conditions["contextflow_structured_handoff"]["tokens"]
    return {
        "benchmark_id": benchmark["task_id"],
        "task_description": benchmark["task_description"],
        "extraction_mode": "deterministic_gold_fixture",
        "conditions": conditions,
        "metrics": {
            "original_token_count": original_tokens,
            "transferred_token_count": transferred_tokens,
            "token_reduction_percent": token_reduction_percent(
                original_tokens, transferred_tokens
            ),
        },
    }


def save_results(results: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )