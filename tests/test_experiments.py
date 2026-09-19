import json

from contextflow.engine.prioritizer import ContextPrioritizer
from contextflow.experiments import load_benchmark, run_benchmark, save_results
from contextflow.metrics import count_tokens, token_reduction_percent
from contextflow.models.task_state import TaskState


def test_run_benchmark_produces_machine_readable_offline_results() -> None:
    results = run_benchmark()

    assert results["benchmark_id"] == "contextflow-experiment-001"
    assert results["extraction_mode"] == "deterministic_gold_fixture"
    assert results["metrics"]["original_token_count"] > 0
    assert results["metrics"]["transferred_token_count"] > 0
    assert "Continue the task" in results["conditions"]["contextflow_structured_handoff"]["continuation_prompt"]


def test_default_benchmark_is_loaded_from_packaged_resource() -> None:
    benchmark = load_benchmark()

    assert benchmark["task_id"] == "contextflow-experiment-001"


def test_token_reduction_and_result_persistence(tmp_path) -> None:
    assert token_reduction_percent(100, 25) == 75.0
    output = tmp_path / "results.json"
    results = run_benchmark()

    save_results(results, output)

    assert json.loads(output.read_text(encoding="utf-8"))["benchmark_id"] == "contextflow-experiment-001"


def test_run_benchmark_can_include_an_injected_summary_baseline() -> None:
    class FakeSummaryProvider:
        def generate(self, prompt: str) -> str:
            return "A short conventional summary."

    results = run_benchmark(summary_provider=FakeSummaryProvider())

    assert results["conditions"]["llm_summary"]["context"] == (
        "A short conventional summary."
    )


def test_experiment_001_handoff_is_smaller_than_verbose_state() -> None:
    results = run_benchmark()
    benchmark_state = TaskState.model_validate(
        load_benchmark()["expected_task_state"]
    )
    verbose = ContextPrioritizer().prioritize(benchmark_state)
    verbose["task_id"] = "contextflow-experiment-001"
    verbose["version"] = 1
    verbose["artifacts"] = benchmark_state.artifacts
    verbose["metadata"] = benchmark_state.metadata

    assert results["conditions"]["contextflow_structured_handoff"]["tokens"] < (
        count_tokens(json.dumps(verbose))
    )
    assert "objective" in results["conditions"]["contextflow_structured_handoff"]["context"]
    assert "pending_tasks" in results["conditions"]["contextflow_structured_handoff"]["context"]