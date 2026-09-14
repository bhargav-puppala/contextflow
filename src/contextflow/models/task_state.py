from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Decision(BaseModel):
    """An important decision made during task execution."""

    model_config = ConfigDict(extra="forbid")

    decision: str = Field(min_length=1)
    reason: str = ""


class FailedAttempt(BaseModel):
    """An approach that failed or was rejected and should not be repeated."""

    model_config = ConfigDict(extra="forbid")

    approach: str = Field(min_length=1)
    result: str = ""
    reason: str = ""


class TaskState(BaseModel):
    """Structured state needed to continue an ongoing task."""

    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    completed_work: list[str] = Field(default_factory=list)
    current_state: str = ""
    failed_attempts: list[FailedAttempt] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    pending_tasks: list[str] = Field(default_factory=list)
    next_action: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)