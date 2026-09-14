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