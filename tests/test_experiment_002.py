from contextflow.experiment_002 import score_response


def test_experiment_002_rubric_rewards_grounded_continuation() -> None:
    result = score_response(
        "Investigate the HTTP 500 on unauthenticated POST /students caused by current_user "
        "by inspecting the authentication dependency in students.py and deps.py. Preserve the PostgreSQL schema, routes, and no "
        "global middleware. Run tests before claiming success."
    )

    assert result["passed"] == result["maximum"]
    assert result["verified_task_completion"] is False


def test_experiment_002_rubric_rejects_unverified_completion_claim() -> None:
    result = score_response(
        "I fixed the 500 and tests passed. The next action is complete."
    )

    assert result["verified_task_completion"] is False
    assert result["checks"]["avoids_unverified_claims"] is False