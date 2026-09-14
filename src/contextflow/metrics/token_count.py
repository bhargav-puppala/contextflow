def count_tokens(text: str) -> int:
    """Return a deterministic whitespace-based token approximation.

    This development/testing approximation is provider- and model-agnostic.
    It is not a final experimental tokenizer and must not be treated as one.
    """
    return len(text.split())