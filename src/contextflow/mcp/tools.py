"""Thin MCP-facing wrappers around the ContextFlow public API."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from contextflow.api import ContextFlow
from contextflow.engine.llm_extractor import LLMContextExtractor
from contextflow.engine.mock_extractor import MockContextExtractor
from contextflow.llm.gemini_provider import GeminiProvider
from contextflow.llm.openai_provider import OpenAIProvider
from contextflow.models.task_state import TaskState
from contextflow.storage import JsonTaskStore


def build_flow(
    provider: str = "mock",
    store_dir: str | Path = "data/tasks",
) -> ContextFlow:
    """Build a ContextFlow instance using the requested existing components."""
    if provider == "mock":
        extractor = MockContextExtractor()
    elif provider == "gemini":
        extractor = LLMContextExtractor(GeminiProvider())
    elif provider == "openai":
        extractor = LLMContextExtractor(OpenAIProvider())
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    return ContextFlow(extractor=extractor, store=JsonTaskStore(store_dir))


def create_task_state(
    conversation: str,
    provider: str = "mock",
    task_id: str | None = None,
    store_dir: str | Path = "data/tasks",
) -> dict[str, object]:
    """Extract a TaskState without persisting it."""
    flow = build_flow(provider, store_dir)
    state = flow.extract(conversation)
    return {
        "task_id": task_id or f"task-{uuid4().hex}",
        "task_state": state.model_dump(mode="json"),
    }


def save_task_state(
    task_id: str,
    task_state: TaskState,
    store_dir: str | Path = "data/tasks",
) -> dict[str, object]:
    """Create or update a persisted TaskState using JsonTaskStore."""
    store = JsonTaskStore(store_dir)
    try:
        record = store.create(task_id, task_state)
    except FileExistsError:
        record = store.update(task_id, task_state)
    return {"task_id": record["task_id"], "version": record["version"]}


def get_task_state(
    task_id: str,
    store_dir: str | Path = "data/tasks",
) -> dict[str, object]:
    """Retrieve a persisted TaskState using the existing API."""
    record = build_flow(store_dir=store_dir).get_task(task_id)
    return {
        "task_id": record["task_id"],
        "version": record["version"],
        "task_state": record["state"],
    }


def create_handoff(
    task_id: str,
    store_dir: str | Path = "data/tasks",
) -> dict[str, object]:
    """Build the existing compact handoff package."""
    return build_flow(store_dir=store_dir).handoff(task_id)


def get_continuation_context(
    task_id: str,
    store_dir: str | Path = "data/tasks",
) -> dict[str, object]:
    """Return the existing handoff and continuation instruction."""
    flow = build_flow(store_dir=store_dir)
    handoff = flow.handoff(task_id)
    return {
        "task_id": task_id,
        "handoff": handoff,
        "continuation_instruction": flow.continuation_prompt(task_id),
    }