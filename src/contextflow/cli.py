import argparse
from collections.abc import Sequence

from contextflow.engine.context_engine import ContextEngine
from contextflow.engine.llm_extractor import LLMContextExtractor
from contextflow.engine.mock_extractor import MockContextExtractor
from contextflow.llm.gemini_provider import GeminiProvider


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ContextFlow pipeline.")
    parser.add_argument(
        "--provider",
        choices=("mock", "gemini"),
        default="mock",
        help="Extraction provider (default: mock)",
    )
    parser.add_argument("conversation", nargs="+", help="Conversation text")
    args = parser.parse_args(argv)

    extractor = (
        LLMContextExtractor(GeminiProvider())
        if args.provider == "gemini"
        else MockContextExtractor()
    )
    result = ContextEngine(extractor).process(" ".join(args.conversation))
    print(result)
    return 0