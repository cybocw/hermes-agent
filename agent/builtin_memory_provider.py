"""Compatibility shim for the legacy builtin memory provider import path.

The built-in memory system was refactored away from a dedicated provider
module, but some tests and downstream integrations still import
``agent.builtin_memory_provider.BuiltinMemoryProvider``. Keep a tiny no-op
provider here so those callers continue to work with the current
``MemoryManager`` API.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from agent.memory_provider import MemoryProvider


class BuiltinMemoryProvider(MemoryProvider):
    """Minimal built-in provider used for compatibility with older imports."""

    @property
    def name(self) -> str:
        return "builtin"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        # Built-in memory is managed elsewhere; this shim intentionally keeps
        # provider initialization side-effect free.
        return None

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return []

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        return json.dumps(
            {
                "success": False,
                "error": f"Builtin memory shim does not handle tool '{tool_name}'",
            }
        )
