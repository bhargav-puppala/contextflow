# ContextFlow

### Token-Efficient Context Handoff for Cross-Agent Task Continuity

ContextFlow is a research-oriented context management system designed to help AI agents continue long-running tasks across agent handoffs without transferring the entire conversation history.

Instead of passing a large conversation from one agent to another, ContextFlow extracts and maintains the **minimum sufficient task state** required for another agent to reliably continue the task.

---

## The Problem

Long-running tasks performed by AI agents can accumulate large amounts of conversational context.

When an agent reaches its context limit, changes models, or hands a task to another agent, a straightforward approach is to transfer the complete conversation history.

This creates several problems:

* High token usage
* Increased inference cost
* Larger context processing overhead
* Redundant or irrelevant information
* Difficulty identifying the actual current state of a task
* Potential loss of important decisions or unfinished work during handoff

The central question behind ContextFlow is:

> **Can a compact, structured representation of the minimum sufficient task state enable a different AI agent to reliably continue an ongoing task while using substantially fewer tokens than transferring the complete conversation history?**

---

## What ContextFlow Does

ContextFlow separates **task execution** from **context management**.

The AI agent performs the task.

ContextFlow manages the information required to preserve continuity.

```text
┌──────────────┐
│    Agent A   │
└──────┬───────┘
       │
       │ Conversation / Task Context
       ▼
┌──────────────────┐
│  Context Engine  │
└────────┬─────────┘
         │
         │ Extract + Structure
         ▼
┌──────────────────┐
│   Task State     │
│                  │
│ Objective        │
│ Constraints      │
│ Decisions        │
│ Completed Work   │
│ Current State    │
│ Failed Attempts  │
│ Artifacts        │
│ Pending Tasks    │
│ Next Action      │
└────────┬─────────┘
         │
         │ Persist / Transfer
         ▼
┌──────────────────┐
│     Agent B      │
└────────┬─────────┘
         │
         ▼
   Continue Task
```

The goal is not simply to summarize a conversation.

The goal is to preserve the **task state necessary for successful continuation**.

---

## Core Concept: Task State

ContextFlow represents an ongoing task using a structured state rather than an unstructured conversation transcript.

A task state may contain:

```json
{
  "objective": "Build a weather application",
  "constraints": [
    "Use a Python-compatible backend"
  ],
  "decisions": [
    {
      "decision": "Use FastAPI",
      "reason": "Better integration with Python-based ML components"
    }
  ],
  "completed_work": [
    "Created frontend structure"
  ],
  "current_state": "Frontend structure created; backend authentication is pending",
  "failed_attempts": [
    {
      "approach": "Node.js backend",
      "reason": "FastAPI better fits the Python-based architecture"
    }
  ],
  "pending_tasks": [
    "Configure weather API authentication"
  ],
  "next_action": "Implement backend authentication"
}
```

This representation allows a receiving agent to understand:

* What needs to be accomplished
* What has already been done
* Which decisions have been made
* Why those decisions were made
* What approaches failed
* What remains unfinished
* What should happen next

---

## Research Direction

ContextFlow is being developed as a research project rather than only as an application.

The primary research direction is **token-efficient context handoff between heterogeneous AI agents**.

We intend to compare ContextFlow against multiple approaches to determine whether structured task-state representations can reduce context size while preserving task continuity.

### Baselines

The initial experimental comparison will include:

1. **Full Conversation History**
2. **Conventional LLM Summary**
3. **Retrieval-Based Context**
4. **ContextFlow Structured Task State**

### Evaluation Metrics

We plan to measure:

* Input tokens
* Output tokens
* Total tokens
* Token reduction percentage
* Task completion / success rate
* Handoff accuracy
* Information retention
* Redundant work after handoff
* Latency
* Estimated inference cost

The exact experimental methodology will be refined after the literature survey and initial implementation.

---

## Experimental Tasks

The evaluation will focus on tasks where maintaining state across multiple agent interactions is important.

Potential categories include:

* Software development
* Debugging and refactoring
* Research tasks
* Data analysis
* Planning and multi-step problem solving

The objective is to determine whether the approach generalizes beyond a single type of task.

---

## Architecture

The planned architecture consists of several modular components:

```text
Agent Adapter
      │
      ▼
Context Ingestion
      │
      ▼
Context Extractor
      │
      ▼
Task-State Builder
      │
      ▼
Context Prioritizer
      │
      ▼
Compression / Selection
      │
      ▼
Persistent Task State
      │
      ▼
Retrieval / Handoff Manager
      │
      ▼
Receiving Agent
```

The system is designed to remain **agent-agnostic**.

Different agents should be able to consume the resulting task state without ContextFlow becoming responsible for executing the underlying task.

---

## Model Context Protocol

Model Context Protocol (MCP) is planned as an interoperability layer for ContextFlow.

MCP can provide a standardized interface through which compatible agents can access task state and context-management capabilities.

However:

> **MCP is an interface mechanism, not the primary research contribution of ContextFlow.**

The research focus remains the representation, extraction, selection, and evaluation of task context for reliable and token-efficient handoff.

## MCP Integration

ContextFlow exposes task-state operations through the official Python MCP SDK. Agent A can provide conversation and task information; ContextFlow converts it into structured `TaskState`, persists that state, and exposes a compact handoff. Agent B can consume the continuation context without receiving the full conversation. MCP is the interoperability layer; ContextFlow remains the context-management engine.

Run the local stdio server with:

```text
python -m contextflow.mcp.server --store-dir data/tasks
```

MCP-compatible clients can inspect and test the server through their MCP Inspector or development command. The default `mock` provider is deterministic and requires no API key; `gemini` and `openai` use the existing provider configuration.

## Use ContextFlow with AI Agents

ContextFlow is a local, agent-agnostic context bridge. Agent A can checkpoint
work, another MCP-compatible agent can retrieve the checkpoint, and both agents
use the same ContextFlow server:

```text
Agent A -> MCP -> ContextFlow TaskState -> MCP -> Agent B
```

1. Clone the repository and create the virtual environment.
2. Install the package with `pip install -e .`.
3. Configure the MCP client with the stdio server below.
4. Have Agent A call `create_task_state`, then `save_task_state`.
5. Close or switch Agent A.
6. Have Agent B call `get_continuation_context` for the same task ID.

Windows PowerShell setup:

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -e .
```

VS Code/GitHub Copilot workspace configuration (`.vscode/mcp.json`):

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

The command is equivalent to:

```text
python -m contextflow.mcp.server --store-dir data/tasks
```

For the complete GitHub Copilot/VS Code setup and manual verification steps,
see [docs/github-copilot.md](docs/github-copilot.md). For another MCP client,
use the same stdio command and adapt only the client's configuration wrapper.

For real conversation extraction, pass `provider` as `gemini` or `openai` to
`create_task_state` and configure `GEMINI_API_KEY` or `OPENAI_API_KEY` in the
server environment. The default `mock` provider is offline and deterministic.
See [docs/agent-compatibility.md](docs/agent-compatibility.md) for the
compatibility matrix and client notes. The local protocol demo can be run with:

```powershell
python examples/mcp_end_to_end.py
```

The demo uses the official Python MCP client and starts the server itself.

In Experiment 001, ContextFlow reduced the transferable context from 2,606
tokens to 494 tokens, an 81.04% reduction. This is a deterministic benchmark
result, not a universal performance claim; real LLM extraction and qualitative
Agent-B continuation are separate evaluation paths.

---

## Current Status

The project is currently in the **research and core architecture phase**.

### Completed

* [x] Project definition
* [x] Research problem formulation
* [x] Initial research questions
* [x] Product specification
* [x] System architecture
* [x] Initial experimental methodology
* [x] Literature survey structure
* [x] 30-paper literature survey set
* [x] GitHub repository setup

### In Progress

* [ ] Task state data model
* [ ] Context extraction pipeline
* [ ] Task-state generation
* [ ] Local persistence
* [ ] Context prioritization
* [ ] Agent handoff mechanism
* [ ] MCP integration
* [ ] Experimental evaluation
* [ ] Baseline implementation
* [ ] Research analysis

---

## MVP

The first implementation will intentionally remain small.

```text
Conversation
     │
     ▼
Context Extractor
     │
     ▼
Task State Builder
     │
     ▼
Structured Task State
     │
     ▼
Local JSON Storage
```

The initial MVP will focus on one fundamental capability:

> **Given a conversation, produce a structured task state containing the information another agent would need to continue the task.**

The MVP will not initially include:

* Complex multi-agent orchestration
* Vector databases
* Cloud infrastructure
* Authentication
* Web UI
* Distributed storage
* Production-scale deployment

These may be considered later if justified by the research and product requirements.

---

## Technology Direction

The current implementation is planned around a lightweight Python stack.

| Component        | Initial Direction             |
| ---------------- | ----------------------------- |
| Language         | Python                        |
| Data validation  | Pydantic                      |
| Testing          | Pytest                        |
| Storage          | JSON / local filesystem       |
| LLM integration  | Configurable model/API        |
| Experiments      | Pandas + Matplotlib           |
| Interoperability | MCP                           |
| Database         | PostgreSQL later, if required |
| UI               | React later, if required      |

The project will prioritize **simplicity, modularity, reproducibility, and measurable results** over unnecessary infrastructure.

---

## Project Structure

The target architecture is organized into independent modules:

```text
src/
└── contextflow/
    ├── models/
    │   ├── task_state.py
    │   ├── context.py
    │   └── handoff.py
    │
    ├── engine/
    │   ├── extractor.py
    │   ├── state_builder.py
    │   ├── prioritizer.py
    │   └── compressor.py
    │
    ├── storage/
    │   ├── interface.py
    │   └── json_store.py
    │
    ├── retrieval/
    │   └── retriever.py
    │
    ├── handoff/
    │   └── manager.py
    │
    ├── adapters/
    │   └── agent.py
    │
    ├── mcp/
    │   └── server.py
    │
    └── config.py
```

This represents the **target architecture**. Components will be implemented incrementally rather than all at once.

## Current Prototype

The repository currently includes:

* Validated `TaskState`, `Decision`, and `FailedAttempt` models
* Deterministic mock and provider-backed extraction
* Deterministic prioritization and compact JSON serialization
* Versioned local JSON task storage
* Machine-readable handoff packages and Agent B continuation prompts
* A small Python API and CLI
* Offline token measurement with `tiktoken` `cl100k_base`
* Experiment 001 benchmark loading, handoff generation, and token metrics

The benchmark runner is evaluation infrastructure, not evidence that the research hypothesis has been proven.

## Installation

Use Python 3.12 or newer:

```text
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Basic Usage

The existing default CLI path uses the deterministic mock extractor and needs no credentials:

```text
python -m contextflow "Build a weather application"
```

The equivalent explicit command is:

```text
python -m contextflow extract --provider mock "Build a weather application"
```

Save and inspect a local task:

```text
python -m contextflow save task-001 "Build a weather application" --store-dir data/tasks
python -m contextflow inspect task-001 --store-dir data/tasks
python -m contextflow handoff task-001 --store-dir data/tasks
python -m contextflow continuation task-001 --store-dir data/tasks
```

The Python API exposes the same core workflow:

```python
from contextflow.api import ContextFlow

flow = ContextFlow()
record = flow.create_task("task-001", "Build a weather application")
handoff = flow.handoff("task-001")
```

## Providers

Gemini extraction requires `GEMINI_API_KEY`, loaded from the environment or a local ignored `.env` file:

```text
python -m contextflow extract --provider gemini "Build a weather application"
```

OpenAI and Gemini providers are tested with injected fake clients. The test suite never requires API credentials or makes network calls.

## Benchmark

Run the deterministic Experiment 001 evaluation prototype:

```text
python -m contextflow experiment --output results/experiment_001.json
```

This compares the full conversation with the structured ContextFlow handoff, generates an Agent B continuation prompt, and records token counts and reduction percentage. The default run uses the benchmark's deterministic gold state fixture and makes no API calls.

To add an LLM-summary baseline, explicitly provide Gemini credentials:

```text
python -m contextflow experiment --provider gemini --output results/experiment_001.json
```

The local `cl100k_base` tokenizer is deterministic and useful for offline comparisons, but it is not Gemini's exact server-side tokenizer. No continuation-agent execution or task-success score is implemented yet.

---

## Development Philosophy

ContextFlow is being developed with two goals in mind:

### 1. Build a useful system

The system should eventually provide a practical way for agents to preserve and exchange task state efficiently.

### 2. Produce measurable research

Claims about efficiency or reliability should be supported by experiments rather than assumptions.

We therefore prioritize:

* Clear baselines
* Reproducible experiments
* Explicit metrics
* Versioned implementations
* Small incremental changes
* Transparent limitations
* Evidence-based conclusions

We will not claim novelty simply because a technique appears to work.

The final research contribution will be determined after systematically comparing existing work with the experimental results.

---

## Documentation

The repository currently contains the following design documents:

* `PRODUCT_SPEC.md` — product definition, scope, MVP, and requirements
* `ARCHITECTURE.md` — system architecture and implementation structure
* `RESEARCH.md` — research questions, hypothesis, methodology, evaluation, and research direction

Additional documentation will be added as implementation progresses.

---

## Roadmap

### Phase 1 — Foundation

* [x] Define research problem
* [x] Define product scope
* [x] Design architecture
* [x] Establish literature survey
* [ ] Implement core data models

### Phase 2 — Context Engine

* [ ] Context ingestion
* [ ] Context extraction
* [ ] Task-state construction
* [ ] Context prioritization
* [ ] Basic compression / selection

### Phase 3 — Persistence & Handoff

* [ ] Persistent task state
* [ ] State versioning
* [ ] Retrieval
* [ ] Handoff manager
* [ ] Agent adapters
* [ ] MCP interface

### Phase 4 — Evaluation

* [ ] Implement baselines
* [ ] Build evaluation tasks
* [ ] Measure token usage
* [ ] Measure task continuity
* [ ] Analyze failure cases
* [ ] Run ablation studies

### Phase 5 — Research & Release

* [ ] Analyze results
* [ ] Refine the system
* [ ] Document limitations
* [ ] Prepare research report / paper
* [ ] Release reproducible experiments

---

## Research Principle

The central design principle of ContextFlow is:

> **ContextFlow manages context. Agents perform tasks.**

The system should preserve the information necessary for an agent to continue a task without unnecessarily carrying the entire history of how the task reached its current state.

---

## Repository

**Project:** ContextFlow
**Repository:** `contextflow`

The project is being developed incrementally with research, architecture, implementation, and evaluation kept as separate but connected concerns.

---

## Status

**Early Research / Prototype**

ContextFlow is an active research project. APIs, architecture, evaluation methodology, and implementation details may change as experimentation and literature analysis progress.
