import tiktoken


_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens with an offline deterministic subword tokenizer.

    ``cl100k_base`` is a real LLM tokenizer suitable for local experiments,
    but it is not Gemini's exact server-side tokenizer.
    """
    return len(_ENCODING.encode(text))


def token_reduction_percent(original_tokens: int, transferred_tokens: int) -> float:
    """Return percentage reduction from original to transferred token counts."""
    if original_tokens <= 0:
        return 0.0
    return round((1 - transferred_tokens / original_tokens) * 100, 2)