from contextflow.engine.compressor import serialize_context
from contextflow.engine.extractor import ConversationContext, ContextExtractor
from contextflow.engine.prioritizer import ContextPrioritizer
from contextflow.engine.state_builder import TaskStateBuilder
from contextflow.models.task_state import TaskState


class ContextEngine:
    """Run extraction, prioritization, and serialization as one pipeline."""

    def __init__(self, extractor: ContextExtractor) -> None:
        self._extractor = extractor
        self._prioritizer = ContextPrioritizer()

    def extract_state(self, context: ConversationContext) -> TaskState:
        extracted = self._extractor.extract(context)
        return (
            extracted
            if isinstance(extracted, TaskState)
            else TaskStateBuilder.build(extracted)
        )

    def process(self, context: ConversationContext) -> str:
        task_state = self.extract_state(context)
        transferable = self._prioritizer.prioritize(task_state)
        return serialize_context(transferable)