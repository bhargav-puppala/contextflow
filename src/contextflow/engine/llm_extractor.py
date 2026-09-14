import json
from json import JSONDecodeError

from contextflow.engine.state_builder import TaskStateBuilder
from contextflow.llm import LLMProvider
from contextflow.models.task_state import TaskState


class LLMContextExtractor:
    """Extract validated task state from conversation text using an LLM provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def extract(self, context: str) -> TaskState:
        prompt = (
            "Extract the task state from this conversation as JSON. "
            "Use the fields objective, constraints, decisions, completed_work, "
            "current_state, failed_attempts, artifacts, pending_tasks, "
            "next_action, and metadata.\n\n"
            f"Conversation:\n{context}"
        )

        response = self._provider.generate(prompt).strip()
        if response.lower().startswith("```json") and response.endswith("```"):
            response = response[7:-3].strip()

        try:
            task_data = json.loads(response)
        except JSONDecodeError as error:
            raise ValueError("LLM provider returned invalid JSON") from error

        return TaskStateBuilder.build(task_data)
