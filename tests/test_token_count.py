from contextflow.metrics import count_tokens


def test_count_tokens_returns_zero_for_empty_text() -> None:
    assert count_tokens("") == 0


def test_count_tokens_counts_simple_whitespace_separated_text() -> None:
    assert count_tokens("Build a weather application") == 4


def test_count_tokens_counts_subword_content() -> None:
    assert count_tokens("unaffordable") > 1


def test_count_tokens_is_deterministic() -> None:
    text = "A repeated measurement should remain stable."

    assert count_tokens(text) == count_tokens(text)