from typing import Protocol


class LLMProvider(Protocol):
    """Provider-neutral interface for generating a response from a prompt."""

    def generate(self, prompt: str) -> str:
        """Generate a response for the supplied prompt."""
        ...