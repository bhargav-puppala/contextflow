import json
from collections.abc import Mapping
from typing import Any


def serialize_context(context: Mapping[str, Any]) -> str:
    """Serialize prioritized transferable context as compact deterministic JSON."""
    if not isinstance(context, Mapping):
        raise TypeError("context must be a mapping")

    return json.dumps(
        context,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )