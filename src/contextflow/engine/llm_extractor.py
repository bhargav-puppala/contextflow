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
            "Extract the task state as one JSON object matching this schema: "
            "objective and current_state and next_action are strings; "
            "constraints, completed_work, artifacts, and pending_tasks are "
            "arrays of strings; decisions is an array of objects with string "
            "fields decision and reason; failed_attempts is an array of objects "
            "with string fields approach, result, and reason; metadata is an "
            "object. Return JSON only, without Markdown fences.\n\n"
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
