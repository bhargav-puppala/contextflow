from collections.abc import Mapping
from typing import Any, Protocol, TypeAlias


ConversationContext: TypeAlias = str | Mapping[str, Any]
StructuredTaskData: TypeAlias = Mapping[str, Any]


class ContextExtractor(Protocol):
    """Provider-neutral interface for extracting structured task data."""

    def extract(self, context: ConversationContext) -> StructuredTaskData:
        """Extract task data from conversation text or structured context."""
        ...