# ContextFlow — System Architecture

**Project:** ContextFlow
**Architecture Version:** 1.0
**Status:** Initial Research Prototype

---

## 1. Architecture Overview

ContextFlow is designed as a modular context-management system that extracts, structures, stores, retrieves, and transfers task context between AI agents.

The architecture separates the following concerns:

1. Agent interaction
2. Context ingestion
3. Context extraction
4. Task-state construction
5. Context prioritization
6. Persistence
7. Retrieval
8. Agent handoff
9. Interoperability through MCP

High-level architecture:

```text
                    ┌──────────────────────┐
                    │       User           │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       Agent A        │
                    │   Task Execution     │
                    └──────────┬───────────┘
                               │
                               │ Interaction / State
                               ▼
                    ┌──────────────────────┐
                    │   ContextFlow API    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Context Engine    │
                    │                      │
                    │  ┌────────────────┐  │
                    │  │ Context        │  │
                    │  │ Extractor      │  │  │
                    │  └───────┬────────┘  │
                    │          ▼           │
                    │  ┌────────────────┐  │
                    │  │ Task-State     │  │
                    │  │ Builder        │  │
                    │  └───────┬────────┘  │
                    │          ▼           │
                    │  ┌────────────────┐  │
                    │  │ Context        │  │
                    │  │ Prioritizer    │  │
                    │  └───────┬────────┘  │
                    └──────────┼───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Task State Store  │
                    └──────────┬───────────┘
                               │
                               │ Retrieval
                               ▼
                    ┌──────────────────────┐
                    │     ContextFlow      │
                    │   Handoff Interface  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       Agent B        │
                    │   Task Continuation  │
                    └──────────────────────┘
```

---

# 2. Core Architectural Principle

The most important architectural principle is:

> **Agents execute tasks; ContextFlow maintains the transferable state of those tasks.**

ContextFlow should not attempt to become another autonomous AI agent.

The system exists between agents and provides task-context management.

---

# 3. Major Components

## 3.1 Agent Adapter

The Agent Adapter provides a consistent interface between an external AI agent and ContextFlow.

Responsibilities:

* Receive task interaction data from an agent.
* Send relevant interaction information to ContextFlow.
* Request task state.
* Submit updates.
* Request handoff context.

The adapter should remain independent of a particular LLM provider.

Conceptually:

```text
Agent
  │
  ▼
Agent Adapter
  │
  ▼
ContextFlow
```

---

# 4. Context Ingestion Layer

The ingestion layer receives information from an active agent.

Potential inputs include:

* User messages
* Agent responses
* Tool results
* Task updates
* Error information
* Artifact references
* Explicit state updates

Example:

```json
{
  "task_id": "task-001",
  "source": "agent_a",
  "type": "interaction",
  "content": "The PostgreSQL database has been configured.",
  "timestamp": "..."
}
```

The ingestion layer should normalize incoming information into a consistent internal representation.

---

# 5. Context Extractor

The Context Extractor identifies information that may be relevant to the ongoing task.

Its job is to transform raw interaction data into candidate task information.

Example:

```text
Raw interaction:

"We initially tried MongoDB but switched to PostgreSQL
because the data has strong relational dependencies."

             ↓

Extracted information:

Decision:
PostgreSQL

Reason:
Strong relational dependencies

Previous approach:
MongoDB
```

The extractor may use an LLM in the initial prototype.

However, the extraction interface should remain modular so that alternative extraction strategies can be evaluated later.

---

# 6. Task-State Builder

The Task-State Builder converts extracted information into the structured Task State.

Initial structure:

```json
{
  "objective": "...",
  "constraints": [],
  "decisions": [],
  "completed_work": [],
  "current_state": "...",
  "failed_attempts": [],
  "errors": [],
  "artifacts": [],
  "pending_tasks": [],
  "next_action": "..."
}
```

The Task-State Builder must support both:

* Creating an initial task state.
* Updating an existing task state.

---

# 7. Task State Model

The Task State is the central data structure of ContextFlow.

A conceptual model:

```text
TaskState
│
├── task_id
├── objective
├── constraints
├── decisions
├── completed_work
├── current_state
├── failed_attempts
├── errors
├── artifacts
├── pending_tasks
├── next_action
└── metadata
```

### Task ID

Uniquely identifies an ongoing task.

### Objective

Describes the desired outcome.

### Constraints

Contains requirements that must continue to be respected.

### Decisions

Contains important decisions and, where available, their reasons.

### Completed Work

Records work already completed.

### Current State

Represents the current status of the task.

### Failed Attempts

Records approaches that should not unnecessarily be repeated.

### Errors

Contains relevant errors affecting task continuation.

### Artifacts

References files, datasets, outputs, commits, or other relevant resources.

### Pending Tasks

Contains incomplete work.

### Next Action

Represents the most appropriate immediate continuation step.

### Metadata

May contain timestamps, version numbers, source-agent information, and other system metadata.

---

# 8. Context Prioritizer

The Context Prioritizer determines which information should receive higher retention priority.

Initial conceptual categories:

```text
CRITICAL
IMPORTANT
OPTIONAL
REDUNDANT
```

Example:

```text
User requirement
        ↓
CRITICAL

Architecture decision
        ↓
CRITICAL

Current task state
        ↓
CRITICAL

Failed approach
        ↓
IMPORTANT

Repeated explanation
        ↓
REDUNDANT
```

The exact prioritization algorithm is a research component and should not be hard-coded as scientifically optimal.

The system must allow alternative prioritization strategies to be evaluated.

---

# 9. Context Compression / Selection

ContextFlow should eventually support selective context reduction.

The goal is not simply to shorten text.

The goal is:

> **Remove information that does not materially affect future task execution while retaining information necessary for reliable continuation.**

Conceptually:

```text
Large Interaction History
          │
          ▼
   Context Analysis
          │
          ▼
 Important Information
          │
          ▼
 Structured Task State
          │
          ▼
Compact Transfer Context
```

The compression/selection layer should be measurable in terms of:

* Input tokens
* Output tokens
* Retained information
* Task performance

---

# 10. Persistent Task State Store

The Task State Store maintains task state independently of an individual agent session.

### Initial implementation

Use local JSON storage.

Example:

```text
data/
└── tasks/
    ├── task-001.json
    ├── task-002.json
    └── ...
```

### Future implementation

Potentially:

```text
Context Engine
      │
      ▼
PostgreSQL
      │
      ├── Task State
      ├── Context Records
      └── Artifact References
```

A vector database should only be introduced if retrieval experiments demonstrate a clear need.

---

# 11. State Versioning

Task state may change over time.

Therefore, updates should ideally be versioned.

Example:

```text
Task State v1
      ↓
Task State v2
      ↓
Task State v3
      ↓
Task State v4
```

This enables:

* Debugging
* Reproducibility
* Experiment analysis
* Rollback
* Comparison between states

The initial MVP may use simple replacement updates, with full versioning added later.

---

# 12. Retrieval Layer

When a receiving agent needs to continue a task, ContextFlow should retrieve the appropriate task state.

Basic flow:

```text
Agent B
   │
   │ Request task context
   ▼
Retrieval Layer
   │
   ▼
Task State Store
   │
   ▼
Relevant Task State
   │
   ▼
Agent B
```

Future versions may support selective retrieval of individual components.

For example:

```text
Get current state
Get pending tasks
Get relevant decisions
Get relevant failed attempts
Get artifact references
```

---

# 13. Handoff Manager

The Handoff Manager coordinates the transition between agents.

A handoff may occur because:

* Agent A reaches a context limit.
* Agent A cannot complete the task.
* A different model is better suited to the next step.
* The user explicitly requests a handoff.
* A task is intentionally distributed across agents.

Handoff flow:

```text
Agent A
   │
   ▼
Handoff Request
   │
   ▼
ContextFlow
   │
   ├── Retrieve current state
   ├── Validate state
   ├── Prepare transfer context
   │
   ▼
Agent B
   │
   ▼
Continue Task
```

---

# 14. MCP Integration

MCP is an interoperability mechanism for exposing ContextFlow capabilities to compatible agents.

MCP should sit at the interface boundary rather than inside the core context-management logic.

Conceptually:

```text
             Agent A
                │
                ▼
          ┌─────────────┐
          │ MCP Client  │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │ MCP Server  │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │ ContextFlow │
          └──────┬──────┘
                 │
                 ▼
             Storage
```

Potential MCP tools:

```text
create_task
get_task_state
update_task_state
save_context
retrieve_context
search_context
prepare_handoff
```

The exact MCP tool interface will be finalized during implementation.

---

# 15. Agent-Agnostic Design

ContextFlow should not depend on one particular AI agent.

Potential future agents could include:

```text
Agent A → Claude
Agent B → GPT
Agent C → Gemini
Agent D → Local LLM
```

The ContextFlow interface should remain consistent.

Example:

```text
Claude
   │
   ├─────────┐
             │
GPT          │
   │         ▼
   ├────→ ContextFlow
             ▲
Gemini       │
   │         │
   └─────────┘
```

This is important because the research focuses on **cross-agent continuity**, not continuity within one particular model.

---

# 16. Model Abstraction

LLM calls should be isolated behind an abstraction layer.

Conceptually:

```text
Context Engine
      │
      ▼
LLM Provider Interface
      │
      ├── Provider A
      ├── Provider B
      └── Provider C
```

This allows experiments to change models without rewriting the Context Engine.

---

# 17. API Design

The initial internal API should remain small.

Possible operations:

```text
POST /tasks
```

Create a task.

```text
GET /tasks/{task_id}
```

Retrieve task state.

```text
POST /tasks/{task_id}/context
```

Submit new context.

```text
PATCH /tasks/{task_id}/state
```

Update task state.

```text
POST /tasks/{task_id}/handoff
```

Prepare context for another agent.

```text
GET /tasks/{task_id}/context
```

Retrieve transferable context.

These are conceptual interfaces. The exact implementation may use direct Python interfaces initially rather than HTTP.

---

# 18. Internal Module Structure

The initial Python package should aim toward a structure similar to:

```text
src/
└── contextflow/
    │
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

This is a target architecture, not a requirement to implement every module immediately.

---

# 19. Dependency Direction

Core logic should not depend directly on infrastructure.

Preferred:

```text
Application
    ↓
Context Engine
    ↓
Interfaces
    ↓
Storage / LLM / MCP implementations
```

Avoid:

```text
Context Engine
    ↓
PostgreSQL-specific code
    ↓
Specific LLM provider
    ↓
MCP-specific logic
```

This keeps the research system modular and testable.

---

# 20. Testing Architecture

Testing should occur at multiple levels.

### Unit Tests

Test:

* Task State validation
* State updates
* Context prioritization
* Extraction parsing
* Storage operations

### Integration Tests

Test:

```text
Context Engine
      ↓
Storage
      ↓
Retrieval
```

### Handoff Tests

Test:

```text
Agent A
   ↓
ContextFlow
   ↓
Agent B
```

### Experiment Tests

Evaluate task continuation across controlled tasks.

---

# 21. Experimental Architecture

The research evaluation should be isolated from the product implementation.

```text
experiments/
│
├── tasks/
├── baselines/
│   ├── full_history/
│   ├── summary/
│   └── retrieval/
│
├── contextflow/
│
├── evaluation/
│
└── results/
```

This prevents experimental code from unnecessarily contaminating the core system.

---

# 22. Baseline Comparison

The architecture should eventually allow:

```text
                    Same Task
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    Full History    Summary     ContextFlow
          │            │            │
          ▼            ▼            ▼
       Agent B       Agent B      Agent B
          │            │            │
          └────────────┼────────────┘
                       ▼
                  Evaluation
```

This is necessary to determine whether ContextFlow provides an actual benefit.

---

# 23. Token Measurement

Token measurement should be implemented independently from the context engine.

The system should record:

```text
input_tokens
output_tokens
total_tokens
context_tokens
```

For each experiment, retain:

```text
task_id
method
model
input_tokens
output_tokens
total_tokens
success
latency
cost
```

This allows reproducible comparisons.

---

# 24. Configuration

Configuration should be separated from source code.

Potential configuration:

```text
configs/
├── default.yaml
├── experiments.yaml
└── models.yaml
```

Configuration may include:

* Model
* Temperature
* Token limits
* Storage backend
* Context strategy
* Experiment parameters

Secrets must never be committed to Git.

Use environment variables for API keys.

---

# 25. Logging

The system should provide structured logging for:

* Task creation
* Context ingestion
* Extraction
* State updates
* Retrieval
* Handoff
* Errors

Logs should help developers reproduce problems without exposing sensitive data unnecessarily.

---

# 26. Security and Privacy

The system may process conversation data that could contain sensitive information.

Therefore:

* API keys must never be committed.
* Secrets must be stored in environment variables.
* Logs should avoid unnecessary sensitive content.
* Stored task data should be treated as potentially sensitive.
* Future deployments should consider authentication and authorization.

Security is not the primary research objective of V1, but the architecture should not ignore it.

---

# 27. MVP Architecture

The first implementation should be significantly smaller than the final architecture.

### MVP:

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
Task State JSON
     │
     ▼
Local Storage
```

The MVP should NOT initially include:

* React
* PostgreSQL
* Vector database
* Complex agent orchestration
* Full MCP integration
* Authentication
* Cloud deployment

These can be added after the core mechanism works.

---

# 28. Implementation Order

Implementation should proceed in this order:

### Step 1

Task State data models.

### Step 2

Local JSON storage.

### Step 3

Context extraction.

### Step 4

Task-state construction and updates.

### Step 5

Context prioritization.

### Step 6

Context retrieval.

### Step 7

Agent handoff.

### Step 8

MCP integration.

### Step 9

Baseline implementations.

### Step 10

Evaluation framework.

### Step 11

Optional API/UI/deployment.

---

# 29. Architectural Success Criteria

The architecture will be considered successful when:

1. An ongoing task can be represented as structured Task State.
2. Task state can persist independently of an agent session.
3. A different agent can retrieve the state.
4. The receiving agent can understand the task's current status.
5. The receiving agent can continue the task without the complete original conversation.
6. Token usage can be measured.
7. The approach can be compared against baseline methods.
8. Different LLM agents can eventually access ContextFlow through a consistent interface.
9. MCP can expose ContextFlow capabilities without coupling the core engine to MCP.
10. Experiments can be reproduced from the repository.

---

# 30. Architecture Principle to Preserve

The most important boundary in the entire project is:

```text
┌──────────────────────────────────────────┐
│              ContextFlow                 │
│                                          │
│  "What information is needed to          │
│   continue this task?"                   │
│                                          │
└──────────────────────────────────────────┘

                    ≠

┌──────────────────────────────────────────┐
│                 Agent                    │
│                                          │
│  "How should I actually perform          │
│   the task?"                             │
│                                          │
└──────────────────────────────────────────┘
```

ContextFlow manages **task context**.

The AI agent performs **task execution**.

Keeping this distinction clear is essential for both the product architecture and the research contribution.
