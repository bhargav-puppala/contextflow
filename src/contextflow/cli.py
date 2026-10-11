import argparse
import json
from collections.abc import Sequence
import sys
from pathlib import Path

from contextflow.api import ContextFlow
from contextflow.demo import run_demo
from contextflow.engine.context_engine import ContextEngine
from contextflow.engine.llm_extractor import LLMContextExtractor
from contextflow.engine.mock_extractor import MockContextExtractor
from contextflow.experiments import run_benchmark, save_results
from contextflow.llm.gemini_provider import GeminiProvider
from contextflow.storage import JsonTaskStore


COMMANDS = {"extract", "save", "inspect", "handoff", "continuation", "experiment", "demo"}


def _extractor(provider: str):
    if provider == "gemini":
        return LLMContextExtractor(GeminiProvider())
    return MockContextExtractor()


def _provider_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--provider",
        choices=("mock", "gemini"),
        default="mock",
        help="Extraction provider (default: mock)",
    )


def _command_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="ContextFlow task tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract")
    _provider_argument(extract_parser)
    extract_parser.add_argument("conversation", nargs="+")

    save_parser = subparsers.add_parser("save")
    _provider_argument(save_parser)
    save_parser.add_argument("task_id")
    save_parser.add_argument("conversation", nargs="+")
    save_parser.add_argument("--store-dir", default="data/tasks")

    for name in ("inspect", "handoff", "continuation"):
        command_parser = subparsers.add_parser(name)
        command_parser.add_argument("task_id")
        command_parser.add_argument("--store-dir", default="data/tasks")

    experiment_parser = subparsers.add_parser("experiment")
    experiment_parser.add_argument("--benchmark")
    experiment_parser.add_argument("--output")
    experiment_parser.add_argument("--provider", choices=("gemini",))
    demo_parser = subparsers.add_parser(
        "demo", help="Run the deterministic offline handoff demonstration"
    )
    demo_parser.add_argument("--output", default="data/demo/handoff.json")
    demo_parser.add_argument("--store-dir", default="data/demo/tasks")
    args = parser.parse_args(argv)

    if args.command == "extract":
        result = ContextEngine(_extractor(args.provider)).process(
            " ".join(args.conversation)
        )
        print(result)
    elif args.command == "save":
        flow = ContextFlow(
            extractor=_extractor(args.provider),
            store=JsonTaskStore(args.store_dir),
        )
        print(json.dumps(flow.create_task(args.task_id, " ".join(args.conversation)), indent=2))
    elif args.command == "inspect":
        record = JsonTaskStore(args.store_dir).get(args.task_id)
        print(json.dumps(record, indent=2, sort_keys=True))
    elif args.command == "handoff":
        flow = ContextFlow(store=JsonTaskStore(args.store_dir))
        print(json.dumps(flow.handoff(args.task_id), indent=2, sort_keys=True))
    elif args.command == "continuation":
        flow = ContextFlow(store=JsonTaskStore(args.store_dir))
        print(flow.continuation_prompt(args.task_id))
    elif args.command == "experiment":
        summary_provider = GeminiProvider() if args.provider == "gemini" else None
        results = (
            run_benchmark(args.benchmark, summary_provider=summary_provider)
            if args.benchmark
            else run_benchmark(summary_provider=summary_provider)
        )
        if args.output:
            save_results(results, args.output)
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print(json.dumps(run_demo(args.output, args.store_dir), indent=2, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if (
        len(arguments) >= 3
        and arguments[0] == "--provider"
        and arguments[2] in COMMANDS
    ):
        arguments = [arguments[2], arguments[0], arguments[1], *arguments[3:]]

    if arguments and arguments[0] in COMMANDS:
        return _command_main(arguments)

    parser = argparse.ArgumentParser(description="Run the ContextFlow pipeline.")
    _provider_argument(parser)
    parser.add_argument("conversation", nargs="+", help="Conversation text")
    args = parser.parse_args(arguments)

    extractor = _extractor(args.provider)
    result = ContextEngine(extractor).process(" ".join(args.conversation))
    print(result)
    return 0