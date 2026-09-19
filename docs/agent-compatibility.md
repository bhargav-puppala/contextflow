# Agent Compatibility

ContextFlow is an agent-agnostic MCP server. Any client that can connect to a
local MCP server over stdio can discover the same tools, resource template, and
continuation prompt. ContextFlow does not execute Agent B; it supplies the
structured state and compact handoff that Agent B uses.

## MCP Server Configuration

Use the repository virtual environment so the `mcp` dependency is available.
The generic stdio configuration is:

```json
{
  "servers": {
    "contextflow": {
      "type": "stdio",
      "command": "C:/Users/bharg/ContextFlow/.venv/Scripts/python.exe",
      "args": [
        "-m",
        "contextflow.mcp.server",
        "--store-dir",
        "C:/Users/bharg/ContextFlow/data/tasks"
      ],
      "cwd": "C:/Users/bharg/ContextFlow"
    }
  }
}
```

On another machine, replace both paths with absolute paths in that checkout.
The equivalent PowerShell launch command is:

```powershell
& .\.venv\Scripts\Activate.ps1
python -m contextflow.mcp.server --store-dir data/tasks
```

## Provider Selection

The MCP `create_task_state` tool accepts `mock`, `gemini`, or `openai`.
`mock` is deterministic and offline. For real extraction, configure the
provider's existing environment variable before starting the MCP client:

```powershell
$env:GEMINI_API_KEY = "..."
# or
$env:OPENAI_API_KEY = "..."
```

The provider call is made by ContextFlow's existing extractor. Tests and the
local demo use `mock` and never require an API key.

## Compatibility Matrix

| Agent | MCP | ContextFlow | Status |
|------|-----|-------------|--------|
| GitHub Copilot | Supported by MCP-capable VS Code clients | Use the stdio configuration above | Supported by MCP; not tested in this repository |
| OpenAI Codex | MCP support depends on the installed Codex client/version | Use the stdio configuration above | Expected to work; not tested in this repository |
| Claude Code | MCP support depends on the installed Claude Code client/version | Use the stdio configuration above | Expected to work; not tested in this repository |
| Gemini CLI | MCP support depends on the installed Gemini CLI version | Use the stdio configuration above | Expected to work; not tested in this repository |
| ChatGPT | Supported only where the selected ChatGPT product exposes custom MCP connections | Use the stdio configuration above where available | Supported where applicable; not tested in this repository |
| Generic MCP client | Yes, using stdio | Use the stdio configuration above | Verified by the automated Python MCP client demo |

The repository has verified the official Python MCP v2 client, server,
Inspector connectivity, tool/resource/prompt discovery, and cross-session task
retrieval. It has not authenticated or run a task inside each external agent.

For GitHub Copilot in VS Code, use the workspace `.vscode/mcp.json` example in
[docs/github-copilot.md](github-copilot.md). Copilot tool invocation is not yet
verified in this repository; the guide gives the manual check required before
claiming that integration.

## Agent-A to Agent-B Workflow

1. Agent A works normally and sends conversation/task information to
   `create_task_state`.
2. Agent A saves the returned state with `save_task_state`.
3. Agent A can stop or switch clients.
4. Agent B calls `get_task_state`, `create_handoff`, or
   `get_continuation_context`, or reads `contextflow://tasks/{task_id}` and
   retrieves `continue_task(task_id)`.
5. Agent B continues from the objective, constraints, decisions, completed
   work, failed attempts, current state, artifacts, pending tasks, and next
   action without receiving Agent A's original conversation.

The reverse direction uses the same server and tools: Agent B can save a new
checkpoint and Agent A can retrieve it. No agent-specific ContextFlow adapter
is required.
