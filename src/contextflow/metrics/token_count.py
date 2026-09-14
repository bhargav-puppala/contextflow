import tiktoken


_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens with an offline deterministic subword tokenizer.

    ``cl100k_base`` is a real LLM tokenizer suitable for local experiments,
    but it is not Gemini's exact server-side tokenizer.
    """
    return len(_ENCODING.encode(text))