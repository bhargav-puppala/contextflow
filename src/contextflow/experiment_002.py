"""Run the controlled local three-arm continuation experiment."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from contextflow.experiments import conversation_text
from contextflow.metrics import count_tokens, token_reduction_percent


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPOSITORY_ROOT / "src" / "contextflow" / "data" / "experiment_001.json"
DEFAULT_STATE = REPOSITORY_ROOT / "data" / "experiment_001_live_extraction.json"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "data" / "experiment_002"
MODEL = "llama3.2:3b"
COMMON_INSTRUCTIONS = """You are the receiving engineer continuing an unfinished software task.

Use only the supplied handoff context. Do not claim that code was changed, tests passed, or the bug was fixed unless the supplied context contains evidence. Provide:
1. The immediate investigation plan.
2. The exact files or symbols to inspect first.
3. The smallest safe code change you would consider, if justified.
4. Tests to run before claiming success.
5. How the plan preserves every recorded constraint.

Do not invent repository contents or completed work. Keep the response actionable and concise.
"""


def ollama_generate(prompt: str, base_url: str = "http://127.0.0.1:11434") -> dict[str, Any]:
    payload = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": 4096},
        }
    ).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=600) as response:
        return json.loads(response.read().decode("utf-8"))


def score_response(response: str) -> dict[str, Any]:
    text = response.lower()
    checks = {
        "identifies_actual_blocker": all(
            phrase in text
            for phrase in ("500", "unauthenticated", "students.py", "current_user")
        ),
        "identifies_correct_next_action": all(
            phrase in text for phrase in ("auth", "depend", "students.py")
        ),
        "preserves_critical_constraints": all(
            phrase in text
            for phrase in ("schema", "postgres", "route", "middleware")
        ),
        "uses_correct_files_or_evidence": all(
            phrase in text for phrase in ("students.py", "deps.py")
        ),
        "avoids_unverified_claims": not any(
            phrase in text
            for phrase in (
                "i fixed",
                "tests passed",
                "successfully implemented",
                "bug is fixed",
            )
        ),
        "actionable_next_step": any(
            phrase in text for phrase in ("inspect", "investigate", "reproduce", "trace")
        ),
    }
    return {
        "checks": checks,
        "passed": sum(checks.values()),
        "maximum": len(checks),
        "verified_task_completion": False,
        "evaluation_type": "deterministic_keyword_rubric",
    }


def _arm_prompt(context: str) -> str:
    return f"{COMMON_INSTRUCTIONS}\nSUPPLIED HANDOFF CONTEXT:\n{context}\n"


def _call_record(prompt: str, response: dict[str, Any], elapsed_ms: float) -> dict[str, Any]:
    return {
        "prompt": prompt,
        "response": response.get("response", ""),
        "raw_usage": {
            key: response.get(key)
            for key in (
                "prompt_eval_count",
                "prompt_eval_duration",
                "eval_count",
                "eval_duration",
                "total_duration",
                "load_duration",
            )
        },
        "wall_time_ms": elapsed_ms,
    }


def _run_call(prompt: str, base_url: str) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = ollama_generate(prompt, base_url)
        return {"status": "completed", **_call_record(prompt, response, round((time.perf_counter() - started) * 1000, 1))}
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        return {
            "status": "failed",
            "prompt": prompt,
            "error": f"{type(error).__name__}: {error}",
            "wall_time_ms": round((time.perf_counter() - started) * 1000, 1),
        }


def run_experiment(
    source_path: str | Path = DEFAULT_SOURCE,
    state_path: str | Path = DEFAULT_STATE,
    output_dir: str | Path = DEFAULT_OUTPUT,
    base_url: str = "http://127.0.0.1:11434",
) -> dict[str, Any]:
    source = json.loads(Path(source_path).read_text(encoding="utf-8"))
    saved_state = json.loads(Path(state_path).read_text(encoding="utf-8"))
    original = conversation_text(source)
    state = json.dumps(saved_state["task_state"], separators=(",", ":"), sort_keys=True)
    arms: dict[str, dict[str, Any]] = {
        "full_history": {"context": original, "preprocessing": None},
        "contextflow": {"context": state, "preprocessing": None},
    }
    summary_prompt = (
        "Write a concise conventional, unstructured summary for another engineer continuing this task. "
        "Include the objective, completed work, current blocker, constraints, failed approaches, pending work, "
        "and next action. Do not use JSON or claim unverified completion.\n\n"
        f"SOURCE CONVERSATION:\n{original}"
    )
    summary_call = _run_call(summary_prompt, base_url)
    arms["normal_summary"] = {
        "context": summary_call.get("response", ""),
        "preprocessing": summary_call,
    }
    for arm in ("full_history", "normal_summary", "contextflow"):
        context = arms[arm]["context"]
        call = _run_call(_arm_prompt(context), base_url)
        arms[arm]["continuation"] = call
        if call["status"] == "completed":
            arms[arm]["evaluation"] = score_response(call["response"])
        arms[arm]["context_tokens_estimate"] = count_tokens(context)

    full_tokens = arms["full_history"]["context_tokens_estimate"]
    for arm in arms.values():
        arm["context_reduction_percent_estimate"] = token_reduction_percent(
            full_tokens, arm["context_tokens_estimate"]
        )
    result = {
        "experiment_id": "contextflow-experiment-002",
        "model": MODEL,
        "source_conversation": str(source_path),
        "state_input": str(state_path),
        "original_conversation_sent_to_contextflow_arm": False,
        "token_estimator": "contextflow.metrics.count_tokens; estimates only",
        "arms": arms,
        "limitations": [
            "Provider-reported counts are not combined across different preprocessing and receiver calls.",
            "Quality is scored by a deterministic keyword rubric, not an independent evaluator.",
            "No task codebase or artifacts from the synthetic conversation are present for fix validation.",
        ],
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    result = run_experiment(output_dir=args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())