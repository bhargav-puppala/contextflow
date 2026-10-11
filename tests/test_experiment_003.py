from urllib.error import URLError

from contextflow.experiment_003 import _is_complete, generate, migrate_checkpoint, run, score


def _response(text: str = "Investigate the dependency and run tests.") -> dict[str, object]:
    return {
        "response": text,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 11,
        "eval_count": 12,
        "eval_duration": 13,
        "total_duration": 14,
        "load_duration": 15,
    }


def test_experiment_003_requests_model_unload_after_each_call(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"response":"ok"}'

    def fake_urlopen(request, timeout):
        captured["payload"] = request.data
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("contextflow.experiment_003.urlopen", fake_urlopen)
    generate("prompt", "http://localhost:11434", 12)

    import json

    assert json.loads(captured["payload"]) ["keep_alive"] == 0
    assert captured["timeout"] == 12


def test_experiment_003_scores_grounded_task_evidence_separately() -> None:
    truth = {
        "facts": ["500", "students.py"],
        "constraints": ["schema", "PostgreSQL"],
        "next_action": ["inspect", "dependency"],
        "forbidden_claims": ["fixed"],
    }
    result = score(
        "Investigate the 500 in students.py. Inspect the dependency wiring. "
        "Preserve the schema and PostgreSQL. Do not claim completion.",
        truth,
    )

    assert result["factual_preservation"] is True
    assert result["constraint_compliance"] is True
    assert result["actionable_continuation"] is True
    assert result["score"] == 4


def test_experiment_003_records_unsupported_claims() -> None:
    truth = {
        "facts": ["blocker"],
        "constraints": ["schema"],
        "next_action": ["inspect"],
        "forbidden_claims": ["tests passed"],
    }
    result = score("The blocker is known; inspect schema. Tests passed.", truth)

    assert result["unsupported_claims"] == ["tests passed"]
    assert result["verified_task_completion"]["status"] == "not_verified"


def test_experiment_003_scoring_handles_negation_and_exposes_item_evidence() -> None:
    truth = {
        "facts": ["blocker|issue"],
        "constraints": ["schema"],
        "next_action": ["inspect"],
        "forbidden_claims": ["fixed"],
    }
    result = score("The issue remains; inspect the schema. Do not claim it is fixed.", truth)

    assert result["factual_preservation"] is True
    assert result["factual_evidence"] == {"blocker|issue": True}
    assert result["unsupported_claims"] == []


def test_experiment_003_filters_and_atomically_checkpoints(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("contextflow.experiment_003.available_ram_gb", lambda: 8.0)
    calls: list[str] = []

    def fake_generate(prompt: str, base_url: str, timeout: float) -> dict[str, object]:
        calls.append(prompt)
        return _response()

    state = run(
        tmp_path,
        task_filter="task-002",
        arm_filter="full_history",
        generate_fn=fake_generate,
    )

    task = next(item for item in state["tasks"] if item["task_id"] == "task-002")
    assert task["arms"]["full_history"]["status"] == "completed"
    assert task["arms"]["normal_summary"]["status"] == "pending"
    assert task["preprocessing"]["status"] == "pending"
    assert len(calls) == 1
    assert (tmp_path / "checkpoint.json").exists()
    assert not list(tmp_path.glob("checkpoint.json.*.tmp"))


def test_experiment_003_resume_skips_completed_calls(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("contextflow.experiment_003.available_ram_gb", lambda: 8.0)
    run(tmp_path, task_filter="task-002", arm_filter="full_history", generate_fn=lambda *args: _response())

    def should_not_run(*args):
        raise AssertionError("completed call was rerun")

    state = run(
        tmp_path,
        resume=True,
        task_filter="task-002",
        arm_filter="full_history",
        generate_fn=should_not_run,
    )
    task = next(item for item in state["tasks"] if item["task_id"] == "task-002")
    assert task["arms"]["full_history"]["status"] == "completed"


def test_experiment_003_success_clears_error_and_preserves_attempt_history(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("contextflow.experiment_003.available_ram_gb", lambda: 8.0)
    run(
        tmp_path,
        task_filter="task-002",
        arm_filter="full_history",
        retries=0,
        generate_fn=lambda *args: (_ for _ in ()).throw(URLError("offline")),
    )

    state = run(
        tmp_path,
        resume=True,
        task_filter="task-002",
        arm_filter="full_history",
        generate_fn=lambda *args: _response(),
    )
    record = next(item for item in state["tasks"] if item["task_id"] == "task-002")["arms"]["full_history"]
    assert record["status"] == "completed"
    assert "error" not in record
    assert "error_kind" not in record
    assert [attempt["status"] for attempt in record["attempt_history"]] == ["failed", "completed"]
    assert "offline" in record["attempt_history"][0]["error"]
    assert record["attempt_history"][1]["usage"]["eval_count"] == 12


def test_experiment_003_does_not_overwrite_checkpoint_without_resume(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("contextflow.experiment_003.available_ram_gb", lambda: 8.0)
    run(tmp_path, task_filter="task-002", arm_filter="full_history", generate_fn=lambda *args: _response())

    import pytest

    with pytest.raises(FileExistsError, match="--resume"):
        run(tmp_path, task_filter="task-002", arm_filter="full_history", generate_fn=lambda *args: _response())


def test_experiment_003_retries_transient_errors_and_records_failures(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("contextflow.experiment_003.available_ram_gb", lambda: 8.0)
    attempts = 0

    def flaky(*args):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise URLError("temporary Ollama failure")
        return _response()

    state = run(tmp_path, task_filter="task-002", arm_filter="full_history", retries=1, generate_fn=flaky)
    task = next(item for item in state["tasks"] if item["task_id"] == "task-002")
    assert task["arms"]["full_history"]["status"] == "completed"
    assert task["arms"]["full_history"]["attempts"] == 2

    state = run(
        tmp_path / "failed",
        task_filter="task-002",
        arm_filter="full_history",
        retries=0,
        generate_fn=lambda *args: (_ for _ in ()).throw(URLError("offline")),
    )
    task = next(item for item in state["tasks"] if item["task_id"] == "task-002")
    assert task["arms"]["full_history"]["status"] == "failed"
    assert task["arms"]["full_history"]["error_kind"] == "URLError"


def test_experiment_003_persists_interruption_and_memory_guard(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("contextflow.experiment_003.available_ram_gb", lambda: 8.0)
    state = run(
        tmp_path / "interrupted",
        task_filter="task-002",
        arm_filter="full_history",
        generate_fn=lambda *args: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    task = next(item for item in state["tasks"] if item["task_id"] == "task-002")
    assert task["arms"]["full_history"]["status"] == "failed"
    assert task["arms"]["full_history"]["error_kind"] == "interrupted"

    monkeypatch.setattr("contextflow.experiment_003.available_ram_gb", lambda: 1.0)
    state = run(
        tmp_path / "low-memory",
        task_filter="task-002",
        arm_filter="full_history",
        generate_fn=lambda *args: _response(),
    )
    task = next(item for item in state["tasks"] if item["task_id"] == "task-002")
    assert task["arms"]["full_history"]["status"] == "blocked"
    assert task["arms"]["full_history"]["error_kind"] == "memory_guard"
    assert _is_complete(state) is False


def test_experiment_003_checkpoint_migration_is_reversible_and_preserves_history(tmp_path) -> None:
    import json

    checkpoint = tmp_path / "checkpoint.json"
    original = {
        "tasks": [{
            "preprocessing": {"status": "pending"},
            "arms": {
                "full_history": {
                    "status": "completed", "response": "kept",
                    "raw_usage": {"eval_count": 4},
                    "error_kind": "memory_guard", "error": "stale",
                },
                "normal_summary": {
                    "status": "failed", "error_kind": "memory_guard", "error": "low RAM",
                },
                "contextflow": {
                    "status": "failed", "error_kind": "URLError", "error": "offline",
                },
            },
        }]
    }
    checkpoint.write_text(json.dumps(original), encoding="utf-8")

    backup, migrated = migrate_checkpoint(checkpoint)

    assert checkpoint.read_text(encoding="utf-8") == backup.read_text(encoding="utf-8")
    arms = json.loads(migrated.read_text(encoding="utf-8"))["tasks"][0]["arms"]
    assert arms["full_history"]["status"] == "completed"
    assert arms["full_history"]["response"] == "kept"
    assert arms["full_history"]["raw_usage"] == {"eval_count": 4}
    assert "error" not in arms["full_history"]
    assert arms["normal_summary"]["status"] == "blocked"
    assert arms["contextflow"]["status"] == "failed"


def test_experiment_003_can_resume_from_migrated_checkpoint_path(tmp_path, monkeypatch) -> None:
    import json

    monkeypatch.setattr("contextflow.experiment_003.available_ram_gb", lambda: 8.0)
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(json.dumps({
        "tasks": [{
            "task_id": "task-002", "description": "fixture", "ground_truth": {
                "facts": [], "constraints": [], "next_action": [], "forbidden_claims": [],
            }, "conversation": "context", "state": {},
            "preprocessing": {"status": "pending"},
            "arms": {arm: {"status": "pending"} for arm in ("full_history", "normal_summary", "contextflow")},
        }],
    }), encoding="utf-8")

    state = run(
        tmp_path, checkpoint_path=checkpoint, resume=True,
        task_filter="task-002", arm_filter="full_history",
        generate_fn=lambda *args: _response(),
    )

    assert state["tasks"][0]["arms"]["full_history"]["status"] == "completed"


def test_experiment_003_completion_rejects_blocked_or_pending_calls() -> None:
    complete_state = {
        "tasks": [{
            "preprocessing": {"status": "completed"},
            "arms": {"full_history": {"status": "completed"},
                      "normal_summary": {"status": "failed"},
                      "contextflow": {"status": "completed"}},
        }],
    }
    assert _is_complete(complete_state) is True
    complete_state["tasks"][0]["arms"]["contextflow"]["status"] = "blocked"
    assert _is_complete(complete_state) is False