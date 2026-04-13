from __future__ import annotations

import importlib.util
import socket
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "hermes_gateway_smoke.py"


def load_module():
    spec = importlib.util.spec_from_file_location("hermes_gateway_smoke", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_copy_runtime_config_copies_config_and_env(tmp_path: Path):
    mod = load_module()
    source_home = tmp_path / "source-home"
    target_home = tmp_path / "target-home"
    source_home.mkdir()
    (source_home / "config.yaml").write_text("model:\n  provider: neo\n", encoding="utf-8")
    (source_home / ".env").write_text("NEO_API_KEY=test-key\n", encoding="utf-8")

    mod.copy_runtime_config(source_home, target_home)

    assert (target_home / "config.yaml").read_text(encoding="utf-8") == "model:\n  provider: neo\n"
    assert (target_home / ".env").read_text(encoding="utf-8") == "NEO_API_KEY=test-key\n"


def test_copy_runtime_config_requires_config_yaml(tmp_path: Path):
    mod = load_module()
    source_home = tmp_path / "source-home"
    source_home.mkdir()

    with pytest.raises(FileNotFoundError):
        mod.copy_runtime_config(source_home, tmp_path / "target-home")


def test_build_gateway_env_sets_required_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    mod = load_module()
    monkeypatch.setenv("EXISTING_VAR", "keep-me")

    hermes_home = tmp_path / "isolated-home"
    workspace = tmp_path / "repo"
    env = mod.build_gateway_env(
        hermes_home=hermes_home,
        workspace=workspace,
        port=9123,
        api_key="smoke-key",
    )

    assert env["EXISTING_VAR"] == "keep-me"
    assert env["HERMES_HOME"] == str(hermes_home)
    assert env["API_SERVER_ENABLED"] == "true"
    assert env["API_SERVER_HOST"] == "127.0.0.1"
    assert env["API_SERVER_PORT"] == "9123"
    assert env["API_SERVER_KEY"] == "smoke-key"
    assert env["MESSAGING_CWD"] == str(workspace)


def test_parse_sse_events_extracts_event_name_and_json_payload():
    mod = load_module()
    raw = (
        "event: tool.started\n"
        'data: {"tool":"read_file","preview":"pyproject.toml"}\n'
        "\n"
        "event: run.completed\n"
        'data: {"final_output":"version=0.8.0"}\n'
        "\n"
    )

    events = list(mod.parse_sse_events(raw))

    assert events == [
        {"event": "tool.started", "data": {"tool": "read_file", "preview": "pyproject.toml"}},
        {"event": "run.completed", "data": {"final_output": "version=0.8.0"}},
    ]


def test_parse_sse_events_promotes_inner_event_name_for_runs_stream():
    mod = load_module()
    raw = 'data: {"event":"run.completed","output":"version=0.8.0"}\n\n'

    events = list(mod.parse_sse_events(raw))

    assert events == [
        {
            "event": "run.completed",
            "data": {"event": "run.completed", "output": "version=0.8.0"},
        }
    ]


def test_collect_final_output_reads_run_completed_output_field():
    mod = load_module()
    events = [
        {
            "event": "message",
            "data": {"event": "message.delta", "delta": "version"},
        },
        {
            "event": "run.completed",
            "data": {"event": "run.completed", "output": "version=0.8.0"},
        },
    ]

    assert mod.collect_final_output(events) == "version=0.8.0"


def test_find_free_port_returns_bindable_local_port():
    mod = load_module()

    port = mod.find_free_port()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", port))
