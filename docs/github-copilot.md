# GitHub Copilot Setup

This guide connects GitHub Copilot in VS Code to the local ContextFlow MCP
server over stdio. The configuration uses the repository's Windows virtual
environment and starts:

```text
python -m contextflow.mcp.server --store-dir data/tasks
```

## Workspace Configuration

The repository includes [.vscode/mcp.json](../.vscode/mcp.json) with the
following current VS Code MCP configuration:

```json
{
  "servers": {
    "contextflow": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/Scripts/python.exe",
      "args": [
        "-m",
        "contextflow.mcp.server",
        "--store-dir",
        "${workspaceFolder}/data/tasks"
      ],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

This is the current VS Code format: `.vscode/mcp.json` uses a top-level
`servers` object and a `type` of `stdio`. The `${workspaceFolder}` variables
make the configuration portable across Windows checkouts. Create the virtual
environment and install ContextFlow first:

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -e .
```

Alternatively, run **MCP: Open Workspace Folder MCP Configuration** in the
Command Palette and paste the configuration above. VS Code may ask you to
trust the local server before starting it.

## Manual Copilot Verification

This repository has not independently verified tool invocation inside GitHub
Copilot, so treat this as the manual integration check:

1. Open the `ContextFlow` repository in VS Code with GitHub Copilot Chat and
   Agent mode enabled.
2. Run **MCP: List Servers** and confirm `contextflow` is listed and running.
3. Open Chat and choose **Configure Tools**. Confirm these tools appear:
   `create_task_state`, `save_task_state`, `get_task_state`, `create_handoff`,
   and `get_continuation_context`.
4. Ask Copilot: `Use ContextFlow to list the available task-state tools.`
   Approve the tool call if prompted.
5. Create or save a task checkpoint, then ask Copilot to retrieve its
   continuation context using the task ID.
6. Use **MCP: Browse Resources** to confirm the
   `contextflow://tasks/{task_id}` resource template, or type the
   `continue_task` MCP prompt when the client exposes server prompts.

Use **MCP: Show Output** or **MCP: List Servers** if the server does not start.
The server writes task data locally under `data/tasks`; it does not require an
API key when the `mock` provider is used.

## Status

- MCP protocol and local Python client: verified by the repository test suite.
- VS Code configuration format: based on the current official VS Code MCP
  configuration reference.
- GitHub Copilot tool invocation: not yet independently verified in this
  repository; complete the manual check above before claiming integration.
