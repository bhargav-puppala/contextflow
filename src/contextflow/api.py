from pathlib import Path
from typing import Any

from contextflow.engine.context_engine import ContextEngine
from contextflow.engine.extractor import ContextExtractor, ConversationContext
from contextflow.engine.mock_extractor import MockContextExtractor
from contextflow.handoff import build_continuation_prompt, build_handoff
from contextflow.models.task_state import TaskState
from contextflow.storage import JsonTaskStore


class ContextFlow:
    """Python API for extraction, persistence, and agent handoff."""

    def __init__(
        self,
        extractor: ContextExtractor | None = None,
        store: JsonTaskStore | None = None,
    ) -> None:
        self._engine = ContextEngine(extractor or MockContextExtractor())
        self._store = store or JsonTaskStore()

    def extract(self, conversation: ConversationContext) -> TaskState:
        return self._engine.extract_state(conversation)

    def process(self, conversation: ConversationContext) -> str:
        return self._engine.process(conversation)

    def create_task(self, task_id: str, conversation: ConversationContext) -> dict[str, Any]:
        return self._store.create(task_id, self.extract(conversation))

    def update_task(self, task_id: str, conversation: ConversationContext) -> dict[str, Any]:
        return self._store.update(task_id, self.extract(conversation))

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self._store.get(task_id)

    def list_tasks(self) -> list[str]:
        return self._store.list_tasks()

    def handoff(self, task_id: str) -> dict[str, Any]:
        record = self.get_task(task_id)
        state = TaskState.model_validate(record["state"])
        return build_handoff(task_id, state, record["version"])

    def continuation_prompt(self, task_id: str) -> str:
        return build_continuation_prompt(self.handoff(task_id))