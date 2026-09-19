"""Run a complete offline ContextFlow MCP client/server demonstration."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


TASK_ID = "mcp-demo-001"
AGENT_A_CONVERSATION = """Agent A is working on a FastAPI + PostgreSQL student-record API.

Objective: build and fix the FastAPI + PostgreSQL student API with JWT
authentication. The current focus is the authentication-related HTTP 500 error
from POST /students, followed by completing the JWT authentication flow.

Constraints: do not change the database schema, do not break existing CRUD
functionality, and preserve the current PostgreSQL setup.

Decision: PostgreSQL remains the database because it is required by the project.
Decision: JWT is the authentication mechanism. Decision: retain the existing
CRUD implementation and make the smallest authentication-only change.

Completed work: database models are implemented; student CRUD endpoints are
implemented; the PostgreSQL connection is configured; and authentication is
partially implemented. The application starts and GET/PUT/DELETE student CRUD
checks still work.

Failed attempt: SQLite was tried initially and abandoned because PostgreSQL is
the required database. A second debugging attempt added a longer database
timeout and extra commit calls, but POST /students still returned HTTP 500, so
the timeout was unrelated to the authentication failure.

Current state: POST /students currently returns HTTP 500. The traceback and
request logging indicate current_user is None because the authentication
dependency is not providing the expected authenticated user. The application
otherwise starts normally and existing CRUD functionality should remain intact.

Pending tasks: fix authentication dependency/current_user handling; complete
the JWT login flow if required; protect the relevant endpoints; add
authentication and integration tests; and run the full test suite.

Next action: inspect the authentication dependency and current_user handling for
the POST /students request.

Irrelevant follow-up from the ongoing conversation: Agent A also rechecked the
README wording, repeated the local server startup command, and confirmed twice
that the PostgreSQL container is already running. Those checks did not change
the diagnosis and should not be treated as completed authentication work.
"""

# The repository's deterministic mock extractor intentionally returns a fixed
# placeholder and does not parse conversation text. Keep extraction in the MCP
# workflow, then send this deterministic realistic state through MCP as the
# offline fixture for the handoff portion of the demonstration.
REALISTIC_TASK_STATE = {
    "objective": (
        "Build and fix a FastAPI + PostgreSQL student API with JWT authentication; "
        "fix the authentication-related 500 error in POST /students."
    ),
    "constraints": [
        "Do not change the database schema.",
        "Do not break existing CRUD functionality.",
        "Preserve the current PostgreSQL setup.",
    ],
    "decisions": [
        {"decision": "Use PostgreSQL as the database.", "reason": "It is required by the project."},
        {"decision": "Use JWT for authentication.", "reason": "It is the selected authentication mechanism."},
        {"decision": "Retain the existing CRUD implementation.", "reason": "Existing CRUD behavior must remain intact."},
    ],
    "completed_work": [
        "Database models implemented.",
        "Student CRUD endpoints implemented.",
        "PostgreSQL connection configured.",
        "Authentication implementation partially completed.",
    ],
    "current_state": (
        "POST /students returns HTTP 500 because current_user is None; the "
        "authentication dependency is not providing the expected authenticated "
        "user. The application starts and existing CRUD functionality works."
    ),
    "failed_attempts": [
        {
            "approach": "Try SQLite instead of PostgreSQL.",
            "result": "Abandoned.",
            "reason": "PostgreSQL is the required database.",
        },
        {
            "approach": "Increase the database timeout and add extra commit calls.",
            "result": "POST /students still returned HTTP 500.",
            "reason": "The failure is in authentication dependency handling, not database timing.",
        },
    ],
    "pending_tasks": [
        "Fix authentication dependency/current_user handling.",
        "Complete the JWT login flow if required.",
        "Protect the relevant endpoints.",
        "Add authentication and integration tests.",
        "Run the full test suite.",
    ],
    "next_action": (
        "Inspect the authentication dependency and current_user handling for the "
        "POST /students request."
    ),
    "metadata": {"source": "offline realistic MCP demo fixture"},
}


def _tool_data(result: Any) -> dict[str, Any]:
    """Read a structured MCP tool result, with a text fallback for compatibility."""
    if result.is_error:
        raise RuntimeError(f"MCP tool failed: {result.content}")
    if result.structured_content is not None:
        return result.structured_content
    for item in result.content:
        if getattr(item, "type", None) == "text":
            return json.loads(item.text)
    raise RuntimeError("MCP tool returned no structured content")


async def run_demo(store_dir: str | Path = "data/tasks", emit: bool = True) -> dict[str, Any]:
    """Run the demo through an MCP stdio client and return its report."""
    root = Path(__file__).resolve().parents[1]
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "contextflow.mcp.server",
            "--store-dir",
            str(Path(store_dir)),
        ],
        cwd=root,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            resources = await session.list_resources()
            resource_templates = await session.list_resource_templates()
            prompts = await session.list_prompts()

            created = _tool_data(
                await session.call_tool(
                    "create_task_state",
                    {
                        "conversation": AGENT_A_CONVERSATION,
                        "provider": "mock",
                        "task_id": TASK_ID,
                    },
                )
            )
            realistic_state = REALISTIC_TASK_STATE
            saved = _tool_data(
                await session.call_tool(
                    "save_task_state",
                    {
                        "task_id": TASK_ID,
                        "task_state": realistic_state,
                    },
                )
            )
            retrieved = _tool_data(
                await session.call_tool("get_task_state", {"task_id": TASK_ID})
            )
            handoff = _tool_data(
                await session.call_tool("create_handoff", {"task_id": TASK_ID})
            )
            continuation = _tool_data(
                await session.call_tool(
                    "get_continuation_context", {"task_id": TASK_ID}
                )
            )
            resource_result = await session.read_resource(
                f"contextflow://tasks/{TASK_ID}"
            )
            resource_state = json.loads(resource_result.contents[0].text)
            prompt_result = await session.get_prompt(
                "continue_task", {"task_id": TASK_ID}
            )
            continuation_prompt = prompt_result.messages[0].content.text

    report = {
        "connection_successful": True,
        "tools_discovered": [tool.name for tool in tools.tools],
        "resources_discovered": [
            resource.uri for resource in resources.resources
        ],
        "resource_templates_discovered": [
            template.uri_template for template in resource_templates.resource_templates
        ],
        "prompts_discovered": [prompt.name for prompt in prompts.prompts],
        "task_id": retrieved["task_id"],
        "structured_state_retrieved": created["task_state"],
        "realistic_state_retrieved": retrieved["task_state"],
        "mock_extraction_result": created["task_state"],
        "saved_version": saved["version"],
        "handoff_generated": handoff,
        "continuation_context_generated": continuation,
        "resource_read_successful": resource_state == retrieved["task_state"],
        "continuation_prompt_retrieved": continuation_prompt,
    }
    if emit:
        print("ContextFlow MCP end-to-end demo")
        print("=" * 34)
        print("MCP connection successful: yes")
        print(f"Tools discovered: {', '.join(report['tools_discovered'])}")
        print(
            "Resources discovered: "
            f"{len(report['resources_discovered'])} concrete, "
            f"{len(report['resource_templates_discovered'])} template"
        )
        print(f"Prompts discovered: {', '.join(report['prompts_discovered'])}")
        print(f"Task ID: {report['task_id']}")
        print("Mock extraction result (the repository mock is intentionally fixed):")
        print(json.dumps(report["mock_extraction_result"], indent=2, sort_keys=True))
        print("Structured state retrieved:")
        print(json.dumps(report["realistic_state_retrieved"], indent=2, sort_keys=True))
        print(f"Handoff generated: {json.dumps(handoff, sort_keys=True)}")
        print(
            "Continuation context generated: "
            f"{json.dumps(continuation, sort_keys=True)}"
        )
        print("Resource successfully read: yes")
        print("Continuation prompt successfully retrieved: yes")
        print("Agent B receives the MCP-generated continuation context only.")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-dir", default="data/tasks")
    args = parser.parse_args()
    asyncio.run(run_demo(args.store_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())