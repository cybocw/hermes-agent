"""Tests for terminal/file tool availability in local dev environments."""

import importlib

from model_tools import get_tool_definitions
from tools.registry import registry
from tools import tool_backend_helpers

terminal_tool_module = importlib.import_module("tools.terminal_tool")


def _registered_terminal_check_globals():
    """Return the globals dict for the currently registered terminal check_fn.

    Some tests reload `tools.terminal_tool`, so patching a stale imported module
    object is not always enough during the full suite. The registry's active
    check function is the source of truth used by `get_tool_definitions()`.
    """
    return registry._tools["terminal"].check_fn.__globals__


class TestTerminalRequirements:
    def test_local_backend_requirements(self, monkeypatch):
        monkeypatch.setitem(
            _registered_terminal_check_globals(),
            "_get_env_config",
            lambda: {"env_type": "local"},
        )
        assert terminal_tool_module.check_terminal_requirements() is True

    def test_terminal_and_file_tools_resolve_for_local_backend(self, monkeypatch):
        monkeypatch.setitem(
            _registered_terminal_check_globals(),
            "_get_env_config",
            lambda: {"env_type": "local"},
        )
        tools = get_tool_definitions(enabled_toolsets=["terminal", "file"], quiet_mode=True)
        names = {tool["function"]["name"] for tool in tools}
        assert "terminal" in names
        assert {"read_file", "write_file", "patch", "search_files"}.issubset(names)

    def test_terminal_and_execute_code_tools_resolve_for_managed_modal(self, monkeypatch, tmp_path):
        terminal_globals = _registered_terminal_check_globals()
        monkeypatch.setenv("HERMES_ENABLE_NOUS_MANAGED_TOOLS", "1")
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
        monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
        monkeypatch.setitem(
            terminal_globals,
            "managed_nous_tools_enabled",
            lambda: True,
        )
        monkeypatch.setattr(tool_backend_helpers, "managed_nous_tools_enabled", lambda: True)
        monkeypatch.setitem(
            terminal_globals,
            "_get_env_config",
            lambda: {"env_type": "modal", "modal_mode": "managed"},
        )
        monkeypatch.setitem(
            terminal_globals,
            "is_managed_tool_gateway_ready",
            lambda _vendor: True,
        )
        tools = get_tool_definitions(enabled_toolsets=["terminal", "code_execution"], quiet_mode=True)
        names = {tool["function"]["name"] for tool in tools}

        assert "terminal" in names
        assert "execute_code" in names
