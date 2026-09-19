import json

from contextflow.experiments import conversation_text, load_benchmark
from contextflow.metrics import count_tokens

def test_experiment_001_benchmark_spec_is_well_formed() -> None:
    benchmark = load_benchmark()

    required_fields = {
        "task_id",
        "task_description",
        "agent_a_conversation",
        "exact_handoff_point",
        "critical_facts",
        "constraints",
        "expected_continuation_requirements",
        "scoring_criteria",
    }
    assert required_fields <= benchmark.keys()
    assert benchmark["task_id"] == "contextflow-experiment-001"
    assert benchmark["agent_a_conversation"]
    assert benchmark["critical_facts"]
    assert benchmark["constraints"]
    assert benchmark["expected_continuation_requirements"]
    assert benchmark["scoring_criteria"]


def test_experiment_001_conversation_contains_required_state_and_irrelevance() -> None:
    benchmark = load_benchmark()
    conversation = " ".join(
        message["content"] for message in benchmark["agent_a_conversation"]
    ).lower()

    for phrase in (
        "chose fastapi",
        "implemented",
        "sqlite was tried initially but abandoned",
        "current state",
        "remaining work",
        "weather is finally nice today",
    ):
        assert phrase in conversation


def test_experiment_001_conversation_is_substantially_longer_than_handoff() -> None:
    benchmark = load_benchmark()
    conversation_tokens = count_tokens(conversation_text(benchmark))

    assert conversation_tokens >= 2000
    assert conversation_tokens <= 5000