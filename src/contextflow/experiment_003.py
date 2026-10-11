"""Run a five-task, three-arm local continuation benchmark."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from contextflow.experiments import conversation_text, load_benchmark
from contextflow.metrics import count_tokens


ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "data" / "experiment_003" / "tasks.json"
LIVE_STATE = ROOT / "data" / "experiment_001_live_extraction.json"
SOURCE = ROOT / "src" / "contextflow" / "data" / "experiment_001.json"
OUTPUT = ROOT / "data" / "experiment_003"
CHECKPOINT = OUTPUT / "checkpoint.json"
RESULTS = OUTPUT / "results.json"
MODEL = "llama3.2:3b"
ARMS = ("full_history", "normal_summary", "contextflow")
INSTRUCTIONS = """You are the receiving engineer continuing an unfinished task.
Use only the supplied context. Do not claim code changed, tests passed, or the task was fixed without evidence.
Return: (1) immediate investigation plan, (2) exact files/symbols to inspect, (3) smallest safe change if justified,
(4) tests before claiming success, and (5) how every constraint is preserved. Do not invent facts.
"""


class MemoryGuardError(RuntimeError):
    """The machine does not have enough free memory for another model call."""


class InterruptedCall(KeyboardInterrupt):
    """A model call was interrupted before a response was received."""


def available_ram_gb() -> float | None:
    """Return available physical RAM, or None when it cannot be reported."""
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                ("total", ctypes.c_ulonglong), ("available", ctypes.c_ulonglong),
                ("page_total", ctypes.c_ulonglong), ("page_available", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
                ("available_extended", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return status.available / (1024**3)
    try:
        import psutil  # type: ignore[import-not-found]
    except ImportError:
        return None
    return psutil.virtual_memory().available / (1024**3)


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def migrate_checkpoint(path: str | Path) -> tuple[Path, Path]:
    """Create a reversible migrated checkpoint without changing the legacy file."""
    source = Path(path)
    state = json.loads(source.read_text(encoding="utf-8"))
    backup = source.with_name(f"{source.name}.legacy.bak")
    suffix = 1
    while backup.exists():
        backup = source.with_name(f"{source.name}.legacy.{suffix}.bak")
        suffix += 1
    shutil.copy2(source, backup)

    for task in state.get("tasks", []):
        records = [task.get("preprocessing", {}), *task.get("arms", {}).values()]
        for record in records:
            if record.get("status") == "completed" and record.get("response") is not None:
                record.pop("error", None)
                record.pop("error_kind", None)
            elif (
                record.get("status") == "failed"
                and record.get("error_kind") == "memory_guard"
                and not record.get("response")
            ):
                record["status"] = "blocked"

    migrated = source.with_name(f"{source.stem}.migrated{source.suffix}")
    _atomic_write(migrated, state)
    return backup, migrated


def generate(prompt: str, base_url: str, timeout_seconds: float) -> dict[str, Any]:
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": 0,
        "options": {"temperature": 0.2, "num_ctx": 4096},
    }).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _transient(error: BaseException) -> bool:
    if isinstance(error, HTTPError):
        return error.code in (408, 429, 500, 502, 503, 504)
    return isinstance(error, (URLError, TimeoutError, ConnectionError, OSError))


def _run_call(
    record: dict[str, Any],
    prompt: str,
    base_url: str,
    timeout_seconds: float,
    retries: int,
    min_free_ram_gb: float,
    generate_fn: Callable[..., dict[str, Any]] = generate,
) -> None:
    record.update({"status": "running", "prompt": prompt, "started_at": time.time(), "ended_at": None})
    record.pop("error", None)
    record.pop("error_kind", None)
    attempts = record.setdefault("attempt_history", [])
    for attempt in range(retries + 1):
        attempt_record: dict[str, Any] = {
            "attempt": len(attempts) + 1,
            "status": "running",
            "started_at": time.time(),
        }
        attempts.append(attempt_record)
        free = available_ram_gb()
        record["memory_before_gb"] = free
        attempt_record["memory_before_gb"] = free
        if free is not None and free < min_free_ram_gb:
            record.update({
                "status": "blocked", "error_kind": "memory_guard",
                "error": f"free RAM {free:.2f} GB below {min_free_ram_gb:.2f} GB",
                "ended_at": time.time(),
            })
            attempt_record.update({"status": "blocked", "error_kind": "memory_guard",
                                   "error": record["error"], "ended_at": time.time()})
            raise MemoryGuardError(record["error"])
        try:
            raw = generate_fn(prompt, base_url, timeout_seconds)
            usage = {key: raw.get(key) for key in (
                "prompt_eval_count", "prompt_eval_duration", "eval_count",
                "eval_duration", "total_duration", "load_duration")}
            record.update({
                "status": "completed", "response": raw.get("response", ""),
                "raw_usage": usage, "attempts": attempt + 1, "ended_at": time.time(),
            })
            record.pop("error", None)
            record.pop("error_kind", None)
            attempt_record.update({"status": "completed", "usage": usage, "ended_at": time.time()})
            return
        except KeyboardInterrupt:
            record.update({
                "status": "failed", "error_kind": "interrupted",
                "error": "KeyboardInterrupt before a completed response",
                "ended_at": time.time(),
            })
            attempt_record.update({"status": "failed", "error_kind": "interrupted",
                                   "error": record["error"], "ended_at": time.time()})
            raise InterruptedCall()
        except Exception as error:
            if attempt < retries and _transient(error):
                attempt_record.update({"status": "failed", "error_kind": type(error).__name__,
                                       "error": str(error), "ended_at": time.time()})
                continue
            record.update({
                "status": "failed", "error_kind": type(error).__name__,
                "error": str(error), "attempts": attempt + 1, "ended_at": time.time(),
            })
            attempt_record.update({"status": "failed", "error_kind": type(error).__name__,
                                   "error": str(error), "ended_at": time.time()})
            return


def _has_evidence(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return all(any(term.lower() in lowered for term in term_group.split("|")) for term_group in terms)


def _matched_terms(text: str, terms: list[str]) -> dict[str, bool]:
    lowered = text.lower()
    return {
        group: any(term.lower() in lowered for term in group.split("|"))
        for group in terms
    }


def _affirmative_forbidden_claim(text: str, phrase: str) -> bool:
    lowered = text.lower()
    start = 0
    while True:
        index = lowered.find(phrase.lower(), start)
        if index < 0:
            return False
        prefix = lowered[max(0, index - 40):index]
        if not any(marker in prefix for marker in ("do not ", "don't ", "not ", "never ")):
            return True
        start = index + len(phrase)


def score(response: str, truth: dict[str, Any]) -> dict[str, Any]:
    lowered = response.lower()
    fact_evidence = _matched_terms(lowered, truth["facts"])
    constraint_evidence = _matched_terms(lowered, truth["constraints"])
    next_action_evidence = _matched_terms(lowered, truth["next_action"])
    facts = all(fact_evidence.values())
    constraints = all(constraint_evidence.values())
    next_action = all(next_action_evidence.values())
    unsupported = [
        claim for claim in truth["forbidden_claims"]
        if _affirmative_forbidden_claim(lowered, claim)
    ]
    return {
        "factual_preservation": facts,
        "factual_evidence": fact_evidence,
        "constraint_compliance": constraints,
        "constraint_evidence": constraint_evidence,
        "actionable_continuation": next_action,
        "action_evidence": next_action_evidence,
        "unsupported_claims": unsupported,
        "avoids_unsupported_completion": not unsupported,
        "verified_task_completion": {"status": "not_verified", "checks": []},
        "score": sum((facts, constraints, next_action, not unsupported)),
        "maximum": 4,
        "scoring_type": "task_specific_text_evidence; not semantic proof",
    }


def _receiver_prompt(context: str) -> str:
    return f"{INSTRUCTIONS}\nSUPPLIED CONTEXT:\n{context}\n"


def _task_one() -> dict[str, Any]:
    benchmark = load_benchmark(SOURCE)
    saved = json.loads(LIVE_STATE.read_text(encoding="utf-8"))
    return {
        "task_id": benchmark["task_id"],
        "description": benchmark["task_description"],
        "conversation": conversation_text(benchmark),
        "state": saved["task_state"],
        "ground_truth": {
            "facts": ["500", "unauthenticated", "students.py", "current_user", "line 47"],
            "constraints": ["schema", "PostgreSQL", "route", "middleware"],
            "next_action": ["investigate", "authentication", "dependency", "students.py", "deps.py"],
            "forbidden_claims": ["fixed", "tests passed", "changed the schema", "reintroduced global middleware"],
        },
    }


def _new_state(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "experiment_id": "contextflow-experiment-003", "model": MODEL,
        "source_fixture": str(SOURCE), "saved_contextflow_state": str(LIVE_STATE),
        "token_estimator": "contextflow.metrics.count_tokens; estimates only",
        "tasks": [{
            "task_id": task["task_id"], "description": task["description"],
            "ground_truth": task["ground_truth"], "conversation": task["conversation"],
            "state": task["state"], "preprocessing": {"status": "pending"},
            "arms": {arm: {"status": "pending"} for arm in ARMS},
            "verified_task_completion": False,
        } for task in tasks],
        "updated_at": None,
    }


def _save(state: dict[str, Any], checkpoint: Path) -> None:
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _atomic_write(checkpoint, state)


def _context(task: dict[str, Any], arm: str, summary: str | None) -> str:
    if arm == "full_history":
        return task["conversation"]
    if arm == "normal_summary":
        return summary or ""
    return json.dumps(task["state"], separators=(",", ":"), sort_keys=True)


def _is_complete(state: dict[str, Any]) -> bool:
    """Only completed or terminal failed calls satisfy the benchmark contract."""
    return all(
        task["preprocessing"]["status"] in ("completed", "failed")
        and all(record["status"] in ("completed", "failed") for record in task["arms"].values())
        for task in state["tasks"]
    )


def run(
    output_dir: str | Path = OUTPUT,
    base_url: str = "http://127.0.0.1:11434",
    checkpoint_path: str | Path | None = None,
    resume: bool = False,
    task_filter: str | None = None,
    arm_filter: str | None = None,
    timeout_seconds: float = 180,
    retries: int = 1,
    min_free_ram_gb: float = 3.0,
    generate_fn: Callable[..., dict[str, Any]] = generate,
) -> dict[str, Any]:
    destination = Path(output_dir)
    checkpoint = Path(checkpoint_path) if checkpoint_path else destination / "checkpoint.json"
    if checkpoint.exists() and not resume:
        raise FileExistsError(f"checkpoint exists; rerun with --resume: {checkpoint}")
    if resume and checkpoint.exists():
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
    else:
        state = _new_state([_task_one(), *json.loads(TASKS.read_text(encoding="utf-8"))])
        _save(state, checkpoint)
    selected_tasks = [task for task in state["tasks"] if task_filter is None or task["task_id"] == task_filter]
    selected_arms = [arm_filter] if arm_filter else list(ARMS)
    try:
        for task in selected_tasks:
            original = task["conversation"]
            summary_record = task["preprocessing"]
            if "normal_summary" in selected_arms and summary_record["status"] != "completed":
                summary_prompt = (
                    "Write a concise conventional unstructured summary for a receiving engineer. Include objective, facts, "
                    "constraints, completed work, blocker, failed approaches, pending work, and next action. Do not use JSON "
                    "or claim unverified completion.\n\nSOURCE:\n" + original
                )
                _run_call(summary_record, summary_prompt, base_url, timeout_seconds, retries, min_free_ram_gb, generate_fn)
                _save(state, checkpoint)
            summary = summary_record.get("response")
            for arm in selected_arms:
                record = task["arms"][arm]
                if record["status"] == "completed":
                    continue
                if arm == "normal_summary" and summary_record["status"] != "completed":
                    record.update({"status": "failed", "error_kind": "preprocessing_failed",
                                   "error": "normal summary did not complete", "ended_at": time.time()})
                    _save(state, checkpoint)
                    continue
                context = _context(task, arm, summary)
                record["context"] = context
                record["context_tokens_estimate"] = count_tokens(context)
                _run_call(record, _receiver_prompt(context), base_url, timeout_seconds, retries, min_free_ram_gb, generate_fn)
                if record["status"] == "completed":
                    record["evaluation"] = score(record["response"], task["ground_truth"])
                _save(state, checkpoint)
            full_tokens = task["arms"]["full_history"].get("context_tokens_estimate") or count_tokens(original)
            for record in task["arms"].values():
                if "context_tokens_estimate" in record:
                    record["context_reduction_percent_estimate"] = round(
                        (full_tokens - record["context_tokens_estimate"]) / full_tokens * 100, 2
                    )
            _save(state, checkpoint)
    except (InterruptedCall, MemoryGuardError):
        _save(state, checkpoint)
    complete = _is_complete(state)
    state["complete"] = complete
    _save(state, checkpoint)
    if complete:
        _atomic_write(destination / "results.json", state)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(OUTPUT))
    parser.add_argument("--checkpoint")
    parser.add_argument("--migrate-checkpoint", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--task")
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--timeout-seconds", type=float, default=180)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--min-free-ram-gb", type=float, default=3.0)
    args = parser.parse_args()
    if args.migrate_checkpoint:
        backup, migrated = migrate_checkpoint(Path(args.output_dir) / "checkpoint.json")
        print(json.dumps({"backup": str(backup), "migrated": str(migrated)}, indent=2))
        return 0
    state = run(
        args.output_dir, checkpoint_path=args.checkpoint, resume=args.resume,
        task_filter=args.task, arm_filter=args.arm,
        timeout_seconds=args.timeout_seconds, retries=args.retries,
        min_free_ram_gb=args.min_free_ram_gb,
    )
    print(json.dumps(state, indent=2))
    return 0 if state.get("complete") else 2


if __name__ == "__main__":
    raise SystemExit(main())