import argparse
from collections.abc import Sequence

from contextflow.engine.context_engine import ContextEngine
from contextflow.engine.mock_extractor import MockContextExtractor


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ContextFlow pipeline.")
    parser.add_argument("conversation", nargs="+", help="Conversation text")
    args = parser.parse_args(argv)

    result = ContextEngine(MockContextExtractor()).process(
        " ".join(args.conversation)
    )
    print(result)
    return 0