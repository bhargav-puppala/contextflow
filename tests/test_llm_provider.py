from contextflow.llm import LLMProvider


class StubLLMProvider:
    def generate(self, prompt: str) -> str:
        return f"response for: {prompt}"


def test_local_stub_implements_llm_provider() -> None:
    provider: LLMProvider = StubLLMProvider()

    assert provider.generate("Summarize the task") == (
        "response for: Summarize the task"
    )