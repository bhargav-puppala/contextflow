import pytest

from contextflow.cli import main


def test_cli_runs_pipeline_and_prints_transferable_context(capsys) -> None:
    exit_code = main(["Build", "a", "weather", "application"])

    assert exit_code == 0
    assert capsys.readouterr().out == (
        '{"completed_work":[],"constraints":[],'
        '"current_state":"Using the mock extractor","decisions":[],'
        '"failed_attempts":[],"next_action":"",'
        '"objective":"Demonstrate deterministic context extraction",'
        '"pending_tasks":[]}\n'
    )


def test_cli_requires_conversation_input() -> None:
    with pytest.raises(SystemExit) as error:
        main([])

    assert error.value.code == 2


def test_cli_gemini_provider_uses_llm_extractor(monkeypatch, capsys) -> None:
    class FakeGeminiProvider:
        def generate(self, prompt: str) -> str:
            return '{"objective":"Extracted by Gemini"}'

    monkeypatch.setattr("contextflow.cli.GeminiProvider", FakeGeminiProvider)

    exit_code = main(["--provider", "gemini", "Build", "an", "application"])

    assert exit_code == 0
    assert '"objective":"Extracted by Gemini"' in capsys.readouterr().out


def test_cli_save_and_handoff_commands(tmp_path, capsys) -> None:
    store_dir = str(tmp_path / "tasks")

    assert main(["save", "task-001", "Build", "an", "API", "--store-dir", store_dir]) == 0
    capsys.readouterr()
    assert main(["handoff", "task-001", "--store-dir", store_dir]) == 0

    output = capsys.readouterr().out
    assert '"task_id": "task-001"' in output
    assert "objective" in output


def test_cli_gemini_save_persists_task_for_default_commands(monkeypatch, tmp_path, capsys) -> None:
    class FakeGeminiProvider:
        def generate(self, prompt: str) -> str:
            return '{"objective":"Extracted by Gemini","pending_tasks":["Add tests"]}'

    monkeypatch.setattr("contextflow.cli.GeminiProvider", FakeGeminiProvider)
    monkeypatch.chdir(tmp_path)

    assert main(
        [
            "--provider",
            "gemini",
            "save",
            "task-002",
            "Build",
            "an",
            "API",
        ]
    ) == 0
    capsys.readouterr()

    assert main(["inspect", "task-002"]) == 0
    inspect_output = capsys.readouterr().out
    assert '"task_id": "task-002"' in inspect_output
    assert '"objective": "Extracted by Gemini"' in inspect_output

    assert main(["handoff", "task-002"]) == 0
    handoff_output = capsys.readouterr().out
    assert '"task_id": "task-002"' in handoff_output

    assert main(["continuation", "task-002"]) == 0
    assert "Continue the task" in capsys.readouterr().out


def test_cli_experiment_command(capsys) -> None:
    assert main(["experiment"]) == 0

    output = capsys.readouterr().out
    assert '"benchmark_id": "contextflow-experiment-001"' in output