"""Official MCP server for ContextFlow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from mcp.server.mcpserver import MCPServer

from contextflow.mcp import tools
from contextflow.models.task_state import TaskState


def create_server(store_dir: str | Path = "data/tasks") -> MCPServer:
    """Create an MCP server bound to a ContextFlow task-store directory."""
    mcp = MCPServer(
        name="contextflow",
        version="0.1.0",
        description="Structured task-state handoff for AI agents.",
    )

    @mcp.tool(structured_output=True)
    def create_task_state(
        conversation: str,
        provider: Literal["mock", "gemini", "openai"] = "mock",
        task_id: str | None = None,
    ) -> dict[str, object]:
        """Create structured TaskState from conversation or task information.

        Use ``mock`` for deterministic offline operation or a configured LLM
        provider for real conversation extraction.
        """
        return tools.create_task_state(conversation, provider, task_id, store_dir)

    @mcp.tool(structured_output=True)
    def save_task_state(task_id: str, task_state: TaskState) -> dict[str, object]:
        """Persist a TaskState checkpoint for another agent to retrieve."""
        return tools.save_task_state(task_id, task_state, store_dir)

    @mcp.tool(structured_output=True)
    def get_task_state(task_id: str) -> dict[str, object]:
        """Retrieve the current structured TaskState checkpoint."""
        return tools.get_task_state(task_id, store_dir)

    @mcp.tool(structured_output=True)
    def create_handoff(task_id: str) -> dict[str, object]:
        """Generate the compact transferable handoff for a task."""
        return tools.create_handoff(task_id, store_dir)

    @mcp.tool(structured_output=True)
    def get_continuation_context(task_id: str) -> dict[str, object]:
        """Return model-independent context for an agent continuing the task."""
        return tools.get_continuation_context(task_id, store_dir)

    @mcp.resource(
        "contextflow://tasks/{task_id}",
        name="task_state",
        description="The current persisted ContextFlow TaskState.",
        mime_type="application/json",
    )
    def task_state_resource(task_id: str) -> str:
        result = tools.get_task_state(task_id, store_dir)
        return json.dumps(result["task_state"], sort_keys=True)

    @mcp.prompt(
        name="continue_task",
        description="Continue work from a persisted ContextFlow task state.",
    )
    def continue_task(task_id: str) -> str:
        return tools.get_continuation_context(task_id, store_dir)[
            "continuation_instruction"
        ]

    return mcp


server = create_server()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ContextFlow MCP server.")
    parser.add_argument("--store-dir", default="data/tasks")
    args = parser.parse_args(argv)
    create_server(args.store_dir).run("stdio")
    return 0


if __name__ == "__main__":
    main()