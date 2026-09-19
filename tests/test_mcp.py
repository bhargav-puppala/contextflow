import asyncio
import json

from contextflow.handoff import build_handoff
from contextflow.mcp.server import create_server
from contextflow.mcp.tools import (
    create_handoff,
    create_task_state,
    get_continuation_context,
    get_task_state,
    save_task_state,
)
from contextflow.models.task_state import TaskState


def run_async(awaitable):
    return asyncio.run(awaitable)


def test_mcp_server_registers_tools_resource_and_prompt(tmp_path) -> None:
    server = create_server(tmp_path)
    tools = run_async(server.list_tools())
    resources = run_async(server.list_resource_templates())
    prompts = run_async(server.list_prompts())

    assert {tool.name for tool in tools} == {
        "create_task_state",
        "save_task_state",
        "get_task_state",
        "create_handoff",
        "get_continuation_context",
    }
    assert resources[0].uri_template == "contextflow://tasks/{task_id}"
    assert prompts[0].name == "continue_task"


def test_mcp_tools_use_mock_extraction_and_persistence(tmp_path) -> None:
    created = create_task_state(
        "Build a deterministic application",
        provider="mock",
        task_id="task-001",
        store_dir=tmp_path,
    )
    state = TaskState.model_validate(created["task_state"])

    assert created["task_id"] == "task-001"
    assert state.objective == "Demonstrate deterministic context extraction"

    saved = save_task_state("task-001", state, tmp_path)
    retrieved = get_task_state("task-001", tmp_path)

    assert saved == {"task_id": "task-001", "version": 1}
    assert retrieved["task_state"] == state.model_dump(mode="json")


def test_mcp_handoff_and_continuation_delegate_to_contextflow(tmp_path) -> None:
    state = TaskState(
        objective="Build an API",
        constraints=["Keep the schema"],
        completed_work=["Created models"],
        failed_attempts=[{"approach": "SQLite", "reason": "PostgreSQL required"}],
        next_action="Add tests",
    )
    save_task_state("task-001", state, tmp_path)

    expected = build_handoff("task-001", state, version=1)
    handoff = create_handoff("task-001", tmp_path)
    continuation = get_continuation_context("task-001", tmp_path)

    assert handoff == expected
    assert continuation["task_id"] == "task-001"
    assert continuation["handoff"] == expected
    assert "Do not redo completed work" in continuation["continuation_instruction"]


def test_mcp_resource_and_prompt_read_current_task(tmp_path) -> None:
    state = TaskState(objective="Build an API", next_action="Add tests")
    save_task_state("task-001", state, tmp_path)
    server = create_server(tmp_path)

    resource = run_async(server.read_resource("contextflow://tasks/task-001"))
    prompt = run_async(server.get_prompt("continue_task", {"task_id": "task-001"}))

    assert json.loads(resource[0].content) == state.model_dump(mode="json")
    assert "Continue the task" in prompt.messages[0].content.text