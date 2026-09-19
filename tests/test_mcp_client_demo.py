import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from examples.mcp_end_to_end import run_demo


def test_mcp_client_demo_uses_stdio_server_end_to_end(tmp_path) -> None:
    report = asyncio.run(run_demo(tmp_path, emit=False))

    assert report["connection_successful"] is True
    assert set(report["tools_discovered"]) == {
        "create_task_state",
        "save_task_state",
        "get_task_state",
        "create_handoff",
        "get_continuation_context",
    }
    assert report["resource_templates_discovered"] == [
        "contextflow://tasks/{task_id}"
    ]
    assert report["prompts_discovered"] == ["continue_task"]
    assert report["task_id"] == "mcp-demo-001"
    assert report["structured_state_retrieved"]["objective"] == (
        "Demonstrate deterministic context extraction"
    )
    assert report["handoff_generated"]["task_id"] == "mcp-demo-001"
    assert report["continuation_context_generated"]["task_id"] == "mcp-demo-001"
    assert report["resource_read_successful"] is True
    assert "Do not redo completed work" in report["continuation_prompt_retrieved"]


def test_task_survives_a_separate_mcp_client_session(tmp_path) -> None:
    asyncio.run(run_demo(tmp_path, emit=False))

    async def retrieve_from_new_session() -> dict:
        root = Path(__file__).parents[1]
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[
                "-m",
                "contextflow.mcp.server",
                "--store-dir",
                str(tmp_path),
            ],
            cwd=root,
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    "get_continuation_context", {"task_id": "mcp-demo-001"}
                )
                return result.structured_content

    continuation = asyncio.run(retrieve_from_new_session())

    assert continuation["task_id"] == "mcp-demo-001"
    assert "POST /students" in continuation["handoff"]["current_state"]
    assert "Do not redo completed work" in continuation["continuation_instruction"]