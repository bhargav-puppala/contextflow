# ContextFlow Technical Documentation

**Package version:** 0.1.2\
**Repository:** https://github.com/bhargav-puppala/contextflow

This document describes the implementation currently present in the
repository and distinguishes implemented behavior from research goals.
See [README.md](../README.md), [ARCHITECTURE.md](../ARCHITECTURE.md),
[PRODUCT_SPEC.md](../PRODUCT_SPEC.md), and [RESEARCH.md](../RESEARCH.md)
for project context.

## 1. Overview

ContextFlow is a Python research prototype for transferring the
operational state of an ongoing task between AI agents or sessions. It
extracts a structured task state, selects fields intended for transfer,
serializes a compact handoff, and can persist the state for later
retrieval.

The intended state captures the objective, constraints, decisions and
rationale, completed work, current state, failed approaches, artifacts,
pending tasks, and next action. ContextFlow manages context; it does not
execute the underlying task, independently verify task completion, or
guarantee that a receiving model follows the handoff correctly.

## 2. Implementation summary

  -----------------------------------------------------------------------
  Area                                Implementation
  ----------------------------------- -----------------------------------
  Language                            Python 3.12+

  Validation                          Pydantic

  Persistence                         Local JSON files

  Serialization                       Deterministic compact JSON

  Token estimates                     tiktoken-based utility

  Extraction                          Mock extractor and LLM-backed
                                      extractor

  Providers                           Gemini and OpenAI

  Agent interface                     MCP server over stdio

  Local continuation experiments      Ollama, configured for
                                      `llama3.2:3b`

  Tests                               pytest

  CLI                                 `python -m contextflow`
  -----------------------------------------------------------------------

Runtime dependencies are declared in `pyproject.toml`. Install pytest
for development and tests.

## 3. Architecture

``` text
Conversation
    |
    v
ContextExtractor
    |
    v
TaskStateBuilder / Pydantic validation
    |
    v
ContextPrioritizer
    |
    v
Compact JSON serialization
    |
    +----> Handoff for Agent B
    |
    +----> JsonTaskStore ----> Python API / MCP
```

The extractor identifies candidate task information. The builder
validates its structure. The prioritizer selects transferable fields.
The serializer creates compact deterministic JSON. The store persists
task versions. The handoff builder packages the transferable state and
continuation instructions. The receiving agent is external to
ContextFlow and consumes the handoff in its own model call.

## 4. Repository map

``` text
src/contextflow/
├── __main__.py, api.py, cli.py
├── demo.py, handoff.py, experiments.py
├── experiment_002.py, experiment_003.py
├── engine/
│   ├── context_engine.py, extractor.py
│   ├── llm_extractor.py, mock_extractor.py
│   ├── state_builder.py, prioritizer.py, compressor.py
├── llm/
│   ├── provider.py, gemini_provider.py, openai_provider.py
├── models/task_state.py
├── storage/json_store.py
├── mcp/server.py, mcp/tools.py
└── data/experiment_001.json

tests/
docs/
examples/
README.md
ARCHITECTURE.md
PRODUCT_SPEC.md
RESEARCH.md
pyproject.toml
requirements.txt
```

-   `api.py`: public Python facade for extraction, create/update,
    retrieval, handoff, and continuation.
-   `cli.py`: CLI operations.
-   `models/task_state.py`: Pydantic schema.
-   `engine/context_engine.py`: orchestrates extraction, validation,
    prioritization, serialization.
-   `engine/llm_extractor.py`: requests JSON task state from a provider
    and validates it.
-   `engine/mock_extractor.py`: fixed deterministic state for
    development; it does not semantically analyze the input
    conversation.
-   `engine/prioritizer.py`: selects transferable fields.
-   `engine/compressor.py`: compact JSON serialization. This is
    structural serialization, not learned or entropy-based compression.
-   `handoff.py`: builds handoff objects and continuation instructions.
-   `storage/json_store.py`: local JSON persistence and version history.
-   `llm/`: provider protocol and Gemini/OpenAI adapters.
-   `mcp/`: MCP tools, resource, prompt, and server.
-   `experiments.py`: fixture-based representation-size benchmark.
-   `experiment_002.py`: one-task, three-condition local comparison.
-   `experiment_003.py`: checkpointed five-task, three-condition
    benchmark runner.
-   `demo.py`: deterministic offline lifecycle demonstration.

## 5. Installation

Requirements: Python 3.12+, Git, and internet access for initial
dependency installation. API keys are needed only for live provider
calls. Ollama and the configured local model are needed for the
continuation experiments.

Windows PowerShell, from the repository root:

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
pip install pytest
python -m pytest -q
```

The project owner reported 78 tests passing in 9.27 seconds after commit
`9f373f6`. This is a recorded local test run, not a claim that a
separate CI workflow passed.

## 6. Provider configuration and security

The mock provider is deterministic and needs no API key.

For Gemini, set `GEMINI_API_KEY` in the process environment or a local
`.env` file. The Gemini adapter calls the Google Gen AI Interactions
API.

For OpenAI, set `OPENAI_API_KEY` in the environment used to start the
process. The current OpenAI adapter does not load `.env` itself, so make
sure the variable is available to the CLI or MCP server process.

Never commit `.env` files, credentials, private conversations, or
sensitive task artifacts. Provider usage and pricing depend on the
provider/model. The default offline demo does not call a live LLM.

## 7. TaskState schema

`TaskState` is defined in `src/contextflow/models/task_state.py`.
Pydantic models reject unexpected fields.

  ---------------------------------------------------------------------------------------
  Field               Type              Requirement/default   Meaning
  ------------------- ----------------- --------------------- ---------------------------
  `objective`         string            Required, non-empty   Intended outcome

  `constraints`       list of strings   Empty list            Requirements/restrictions

  `decisions`         list of           Empty list            Decisions and rationale
                      `Decision`                              

  `completed_work`    list of strings   Empty list            Work reported as complete

  `current_state`     string            Empty string          Current known state

  `failed_attempts`   list of           Empty list            Failed/rejected approaches
                      `FailedAttempt`                         

  `artifacts`         list of strings   Empty list            File/artifact references

  `pending_tasks`     list of strings   Empty list            Remaining work

  `next_action`       string            Empty string          Suggested next step

  `metadata`          object            Empty dictionary      Additional metadata
  ---------------------------------------------------------------------------------------

`Decision` has a required non-empty `decision` and optional `reason`.
`FailedAttempt` has a required non-empty `approach` and optional
`result` and `reason`.

Example:

``` json
{
  "objective": "Resolve an authentication failure",
  "constraints": ["Preserve the existing database schema"],
  "decisions": [{"decision": "Inspect the auth dependency", "reason": "The failure occurs before the route handler"}],
  "completed_work": ["Reproduced the failing request"],
  "current_state": "The endpoint returns an authentication error",
  "failed_attempts": [{"approach": "Change the schema", "result": "Not attempted", "reason": "No evidence points to the schema"}],
  "artifacts": ["src/app/deps.py"],
  "pending_tasks": ["Trace dependency resolution", "Run regression tests"],
  "next_action": "Inspect the authentication dependency",
  "metadata": {"source": "example"}
}
```

This is a schema example, not a claim about a real application. A state
records what an extractor or caller says; a `completed_work` entry is
not independent proof that work occurred. Stronger guarantees require
evidence, provenance, test results, or an explicit verification status.

## 8. Extraction, prioritization, and handoff

The mock extractor returns a fixed state for plumbing and tests; it does
not extract facts from input text. The LLM extractor asks the selected
provider for one JSON object, parses it, and validates it as
`TaskState`. Invalid JSON raises `ValueError`; schema violations are
surfaced by Pydantic. Structural validation does not prove factual
accuracy.

The prioritizer selects `objective`, `constraints`, `decisions`,
`completed_work`, `current_state`, `failed_attempts`, `pending_tasks`,
and `next_action`. The handoff builder removes empty values and includes
`artifacts` when present. Metadata is not transferred in the current
handoff.

The serializer uses compact JSON separators and sorted keys. This makes
output deterministic but does not prove the representation is minimal or
sufficient for every task. A handoff includes a task ID, version, and
non-empty transferable fields. The continuation instruction asks the
receiving agent to respect constraints, avoid repeating failed attempts,
and choose an appropriate next action.

## 9. Persistence and versioning

`JsonTaskStore` writes one JSON file per task under `data/tasks` by
default.

-   Creation starts at version 1 and raises `FileExistsError` if the
    task already exists.
-   Updating appends the previous version/state to history and writes
    the replacement with an incremented version.
-   Retrieving a missing task raises `FileNotFoundError`.
-   Task IDs must be non-empty and filename-safe; path components are
    rejected.
-   Listing derives task IDs from JSON filenames.

This lightweight store does not provide encryption at rest, access
control, database transactions, distributed coordination, or
production-grade concurrent-write handling. Treat task files as
sensitive.

## 10. CLI reference

Run commands from the repository root.

### Offline demo

``` powershell
python -m contextflow demo
python -m contextflow demo --output data/demo/handoff.json --store-dir data/demo/tasks
```

The demo loads the deterministic expected-state fixture from Experiment
001, saves and reloads a handoff, and prints a deterministic
continuation plan. It does not call an LLM and does not show that an LLM
independently solved the task. Its token reduction is a fixture-level
representation measurement, not end-to-end savings.

### Extract

``` powershell
python -m contextflow extract --provider mock "The API returns an authentication error."
python -m contextflow extract --provider gemini "The API returns an authentication error."
```

The CLI selector currently exposes `mock` and `gemini`. OpenAI is
available through the provider abstraction and MCP configuration but is
not a choice in this CLI selector.

### Create, inspect, handoff, continue

``` powershell
python -m contextflow save task-001 --provider mock "Investigate the authentication error" --store-dir data/tasks
python -m contextflow inspect task-001 --store-dir data/tasks
python -m contextflow handoff task-001 --store-dir data/tasks
python -m contextflow continuation task-001 --store-dir data/tasks
```

CLI `save` creates a new task and errors if the ID already exists.

### Fixture benchmark

``` powershell
python -m contextflow experiment
python -m contextflow experiment --output data/experiment-results.json
python -m contextflow experiment --provider gemini --output data/experiment-results.json
```

The standard benchmark compares the full conversation with a handoff
built from the checked-in expected-state fixture. It is mainly a
representation-size comparison, not a live extraction accuracy test. If
a summary provider is used, report its preprocessing cost separately.

## 11. MCP interface

Start the stdio server:

``` powershell
python -m contextflow.mcp.server --store-dir data/tasks
```

The package also declares the `contextflow-mcp` console entry point. An
MCP-compatible client launches the server as a local subprocess.

  -----------------------------------------------------------------------
  Tool                                Purpose
  ----------------------------------- -----------------------------------
  `create_task_state`                 Extract and return structured
                                      state; provider can be mock,
                                      Gemini, or OpenAI

  `save_task_state`                   Create or update a persisted
                                      checkpoint

  `get_task_state`                    Retrieve state and version

  `create_handoff`                    Return compact handoff for a task

  `get_continuation_context`          Return handoff plus continuation
                                      instruction
  -----------------------------------------------------------------------

The server also exposes `contextflow://tasks/{task_id}` as a resource
pattern and `continue_task` as a prompt. See
[github-copilot.md](github-copilot.md) and
[agent-compatibility.md](agent-compatibility.md) for client
configuration notes. MCP is an interoperability layer, not the primary
research contribution.

## 12. Experiments and reproducibility

These are distinct evaluation paths and should not be combined as if
they were one benchmark.

### Fixture-based benchmark

`python -m contextflow experiment` uses the checked-in Experiment 001
conversation and expected task-state fixture. It estimates
representation size. It does not prove a model extracted the state
correctly or that a receiving agent completed the task.

### Experiment 002

`src/contextflow/experiment_002.py` compares full history, a locally
generated conventional summary, and a serialized ContextFlow state for
one debugging task. It uses the local Ollama HTTP endpoint and is
configured for `llama3.2:3b`.

``` powershell
python -m contextflow.experiment_002
python -m contextflow.experiment_002 --output-dir data/experiment_002
```

It records outputs, available Ollama usage fields, representation
estimates, and a deterministic keyword-oriented rubric. This is a
one-task exploratory comparison, not a generalizable evaluation. The
score does not independently establish semantic correctness or verified
task completion.

### Experiment 003

`src/contextflow/experiment_003.py` is designed for five tasks and three
conditions: full history, conventional summary, and ContextFlow state.
It uses local Ollama with `llama3.2:3b`. Features include checkpoints,
resume support, task/arm filters, selected transient retries, timeout
configuration, a free-RAM guard, and a final results file written when
the runner considers the benchmark complete.

``` powershell
python -m contextflow.experiment_003
python -m contextflow.experiment_003 --resume
python -m contextflow.experiment_003 --resume --task task-001
python -m contextflow.experiment_003 --resume --arm contextflow
python -m contextflow.experiment_003 --resume --timeout-seconds 180 --retries 1 --min-free-ram-gb 3
```

A fresh run refuses to overwrite an existing checkpoint unless
`--resume` is selected. Inspect checkpoints before resuming or migrating
and preserve the original before migration.

**Important reproducibility limitation:** `.gitignore` excludes the root
`data/` directory except for the Experiment 001 fixture under
`src/contextflow/data`. Experiment 002 and Experiment 003 refer to local
extraction artifacts and task fixtures under `data/`; not all required
inputs are included in a clean public clone. Therefore, these
continuation experiments are not fully reproducible from the public
repository alone unless the inputs are supplied or a fixture-generation
path is added. Do not report Experiment 003 as complete unless all
conditions have finished and the final results file exists.

### Token-counting rules

Keep separate:

-   **Representation size:** estimated tokens in handoff or summary.
-   **Receiver usage:** tokens consumed by the receiving model.
-   **Preprocessing usage:** tokens used to create a summary or extract
    state.
-   **End-to-end usage:** a defined total of the relevant workflow
    components.

``` text
reduction_percent = (full_history_tokens - representation_tokens)
                    / full_history_tokens * 100
```

This formula alone does not measure end-to-end savings. Record
tokenizer, model, prompt template, preprocessing usage, receiving usage,
latency, and scoring method. Do not combine provider-reported and
estimated token counts without explaining the accounting.

## 13. Testing

``` powershell
python -m pytest -q
```

The suite covers state, extraction/handoff, storage, demo, and
experiment-runner behavior. Passing tests supports correctness of tested
paths; it does not establish research validity, task success, or
generalization.

## 14. Troubleshooting

-   **Gemini missing key:** set `GEMINI_API_KEY` in the process
    environment or local `.env` file and verify it is visible to the
    same Python process.
-   **OpenAI missing key:** set `OPENAI_API_KEY` in the environment used
    to start the CLI or MCP server. The current adapter does not load
    `.env` itself.
-   **Unexpected mock output:** mock extraction is deterministic and
    does not analyze conversation text; use a configured LLM provider
    for real extraction.
-   **Task already exists:** CLI `save` creates a new task. Use the
    Python API `update_task` method or MCP `save_task_state` tool for
    versioned updates.
-   **Ollama connection failure:** ensure Ollama is running and the
    configured model is available at `127.0.0.1:11434`.
-   **Experiment 003 memory guard:** the runner can block calls when
    free RAM is below its configured threshold. Inspect the checkpoint;
    do not count blocked calls as completed.
-   **No Experiment 003 `results.json`:** inspect `checkpoint.json` for
    pending, blocked, or interrupted calls. Final output is written only
    after the runner's completion contract is satisfied.
-   **Git `.test-tmp` permission warning:** this is a local filesystem
    warning, not proof of test failure. Inspect the directory and
    owner/process before deleting it or changing permissions.

## 15. Security and limitations

-   Treat conversation text, task files, handoffs, and experiment
    outputs as potentially sensitive.
-   Do not commit credentials, private conversations, or unreviewed
    generated results.
-   Local JSON storage is not encrypted and has no access control.
-   LLM extraction is not a source of truth; verify important facts
    against original artifacts.
-   Extracting state does not mean the receiving agent completed the
    task.
-   The prioritizer is deterministic and field-based; it does not
    establish a mathematically minimum sufficient representation.
-   Evaluation is exploratory and has limited task coverage.
-   This is a research prototype, not a hardened multi-user production
    service.

## 16. Status and research work remaining

Implemented: structured TaskState schema and validation; mock and LLM
extraction interfaces; Gemini/OpenAI adapters; deterministic
prioritization and compact JSON serialization; local JSON persistence
with history; Python API and CLI; MCP tools/resource/prompt/server;
offline demo; fixture-based benchmark; single-task and planned five-task
experiment runners; automated tests.

Research work still needed:

1.  Complete the multi-task evaluation across all conditions and publish
    the inputs required to reproduce it.
2.  Improve semantic scoring with blinded human review and task-specific
    verification.
3.  Standardize end-to-end token accounting across preprocessing and
    receiving calls.
4.  Compare against clearly specified baselines; include retrieval only
    when that baseline is implemented.
5.  Verify related literature and avoid unsupported novelty or
    superiority claims.

When reporting results, identify the repository commit, task fixture,
provider/model version, local model configuration, and token-counting
method. Keep measured results, intended behavior, and future work
clearly separated.
