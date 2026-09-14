from contextflow.engine.extractor import (
    ConversationContext,
    StructuredTaskData,
)


class MockContextExtractor:
    """Deterministic extractor for development and testing."""

    def extract(self, context: ConversationContext) -> StructuredTaskData:
        return {
            "objective": "Demonstrate deterministic context extraction",
            "current_state": "Using the mock extractor",
            "metadata": {"extractor": "mock"},
        }