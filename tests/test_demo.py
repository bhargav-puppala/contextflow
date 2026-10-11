import json

from contextflow.cli import main
from contextflow.demo import run_demo


def test_offline_demo_persists_and_reloads_handoff(tmp_path) -> None:
    result = run_demo(tmp_path / "handoff.json", tmp_path / "tasks")

    assert result["extraction_mode"] == "deterministic_expected_task_state_fixture"
    assert result["fresh_session"]["loaded_from_store"] is True
    assert result["fresh_session"]["original_conversation_provided"] is False
    assert result["fresh_session"]["continuation_response"].startswith(
        "Offline continuation (deterministic; not an LLM response)"
    )
    assert result["token_estimates"]["original_conversation"] > (
        result["token_estimates"]["handoff"]
    )
    assert json.loads((tmp_path / "handoff.json").read_text(encoding="utf-8"))["objective"]
    assert (tmp_path / "tasks" / "contextflow-experiment-001.json").exists()


def test_cli_demo_is_offline_and_writes_requested_output(tmp_path, capsys) -> None:
    output = tmp_path / "handoff.json"
    assert main(["demo", "--output", str(output), "--store-dir", str(tmp_path / "tasks")]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["demo"] == "offline_contextflow_handoff"
    assert result["handoff_path"] == str(output)