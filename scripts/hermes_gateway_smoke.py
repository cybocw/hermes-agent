#!/usr/bin/env python3
"""End-to-end smoke test for the Hermes gateway API server.

This script starts the gateway against an isolated HERMES_HOME, probes the
OpenAI-compatible HTTP endpoints, prints a compact summary, and then shuts the
gateway back down.

Run from the repo root after activating the project virtualenv:

    source venv/bin/activate
    python scripts/hermes_gateway_smoke.py
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

import requests


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_HOME = Path.home() / ".hermes"
DEFAULT_API_KEY = "hermes-smoke-key"
DEFAULT_CHAT_PROMPT = "请只回复 GATEWAY_OK"
DEFAULT_CHAT_EXPECT = "GATEWAY_OK"
DEFAULT_RUN_PROMPT = "请读取 pyproject.toml，只回复 version=<版本号>"
DEFAULT_RUN_EXPECT = "version="


def find_free_port() -> int:
    """Ask the OS for a free local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def copy_runtime_config(source_home: Path, target_home: Path) -> None:
    """Copy the minimum config needed for an isolated gateway smoke run."""
    config_path = source_home / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing required config: {config_path}")

    target_home.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_path, target_home / "config.yaml")

    env_path = source_home / ".env"
    if env_path.exists():
        shutil.copy2(env_path, target_home / ".env")


def build_gateway_env(hermes_home: Path, workspace: Path, port: int, api_key: str) -> dict[str, str]:
    """Build the isolated environment used for the smoke gateway process."""
    env = os.environ.copy()
    env["HERMES_HOME"] = str(hermes_home)
    env["API_SERVER_ENABLED"] = "true"
    env["API_SERVER_HOST"] = "127.0.0.1"
    env["API_SERVER_PORT"] = str(port)
    env["API_SERVER_KEY"] = api_key
    env["MESSAGING_CWD"] = str(workspace)
    return env


def parse_sse_events(raw: str) -> list[dict[str, Any]]:
    """Parse a small SSE transcript into event dictionaries."""
    events: list[dict[str, Any]] = []
    event_name: str | None = None
    data_lines: list[str] = []

    def flush() -> None:
        nonlocal event_name, data_lines
        if event_name is None and not data_lines:
            return
        data_text = "\n".join(data_lines).strip()
        payload: Any = data_text
        if data_text:
            try:
                payload = json.loads(data_text)
            except json.JSONDecodeError:
                payload = data_text
        resolved_event = event_name or "message"
        if (
            event_name is None
            and isinstance(payload, dict)
            and isinstance(payload.get("event"), str)
            and payload["event"]
        ):
            resolved_event = payload["event"]
        events.append({"event": resolved_event, "data": payload})
        event_name = None
        data_lines = []

    for line in raw.splitlines():
        if not line:
            flush()
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
            continue
        if line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].strip())

    flush()
    return events


def _tail_text(path: Path, max_lines: int = 80) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-max_lines:])


def _request_json(method: str, url: str, timeout: float, headers: dict[str, str] | None = None,
                  payload: dict[str, Any] | None = None) -> requests.Response:
    response = requests.request(method, url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return response


def wait_for_health(base_url: str, timeout: float) -> dict[str, Any]:
    """Poll /health until the gateway comes up or time out."""
    deadline = time.time() + timeout
    last_error = "health check did not succeed"
    while time.time() < deadline:
        try:
            response = _request_json("GET", f"{base_url}/health", timeout=5.0)
            return response.json()
        except Exception as exc:  # pragma: no cover - exercised in real smoke
            last_error = str(exc)
            time.sleep(0.25)
    raise RuntimeError(f"Gateway did not become healthy before timeout: {last_error}")


def start_gateway(log_path: Path, env: dict[str, str]) -> subprocess.Popen[str]:
    """Start the gateway process with output redirected to a log file."""
    log_handle = open(log_path, "w", encoding="utf-8")
    return subprocess.Popen(
        [sys.executable, "-m", "hermes_cli.main", "gateway", "run"],
        cwd=REPO_ROOT,
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )


def stop_gateway(proc: subprocess.Popen[str], timeout: float = 10.0) -> None:
    """Terminate the gateway process, escalating to kill if needed."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=timeout)


def run_chat_probe(base_url: str, api_key: str, prompt: str, timeout: float,
                   session_id: str | None = None) -> tuple[requests.Response, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if session_id:
        headers["X-Hermes-Session-Id"] = session_id
    payload = {
        "model": "hermes-agent",
        "messages": [{"role": "user", "content": prompt}],
    }
    response = _request_json(
        "POST",
        f"{base_url}/v1/chat/completions",
        headers=headers,
        payload=payload,
        timeout=timeout,
    )
    response_session_id = response.headers.get("X-Hermes-Session-Id", "")
    return response, response_session_id


def extract_chat_text(response: requests.Response) -> str:
    body = response.json()
    return body["choices"][0]["message"]["content"]


def _iter_sse_events(lines: Iterable[str]) -> Iterable[dict[str, Any]]:
    buffer: list[str] = []
    for line in lines:
        if line == "":
            raw = "\n".join(buffer).strip()
            buffer = []
            if raw:
                for event in parse_sse_events(raw + "\n\n"):
                    yield event
            continue
        buffer.append(line)
    raw = "\n".join(buffer).strip()
    if raw:
        for event in parse_sse_events(raw + "\n\n"):
            yield event


def run_async_probe(base_url: str, api_key: str, prompt: str, timeout: float) -> tuple[str, list[dict[str, Any]]]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    run_response = _request_json(
        "POST",
        f"{base_url}/v1/runs",
        headers=headers,
        payload={"input": prompt, "tools": ["file"]},
        timeout=timeout,
    )
    if run_response.status_code != 202:
        raise RuntimeError(f"Expected 202 from /v1/runs, got {run_response.status_code}")
    run_id = run_response.json()["run_id"]

    events_response = requests.get(
        f"{base_url}/v1/runs/{run_id}/events",
        headers={"Authorization": f"Bearer {api_key}"},
        stream=True,
        timeout=(5.0, timeout),
    )
    events_response.raise_for_status()

    events: list[dict[str, Any]] = []
    for event in _iter_sse_events(events_response.iter_lines(decode_unicode=True)):
        events.append(event)
        if event["event"] == "run.completed":
            break

    return run_id, events


def collect_final_output(events: list[dict[str, Any]]) -> str:
    for event in reversed(events):
        data = event.get("data")
        if isinstance(data, dict):
            for key in ("final_output", "content", "output_text", "output"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    return value
    return ""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an isolated Hermes gateway API smoke test.")
    parser.add_argument("--source-home", type=Path, default=DEFAULT_SOURCE_HOME, help="Hermes home to copy config from.")
    parser.add_argument("--workspace", type=Path, default=REPO_ROOT, help="Workspace exposed to the gateway agent.")
    parser.add_argument("--port", type=int, default=0, help="Port to bind. Default 0 picks a free local port.")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="Temporary bearer token for the local smoke run.")
    parser.add_argument("--startup-timeout", type=float, default=30.0, help="Seconds to wait for /health.")
    parser.add_argument("--request-timeout", type=float, default=120.0, help="Seconds allowed for chat/run requests.")
    parser.add_argument("--chat-prompt", default=DEFAULT_CHAT_PROMPT, help="Prompt for /v1/chat/completions.")
    parser.add_argument("--expect-chat-substring", default=DEFAULT_CHAT_EXPECT, help="Required substring in chat output.")
    parser.add_argument("--run-prompt", default=DEFAULT_RUN_PROMPT, help="Prompt for /v1/runs.")
    parser.add_argument("--expect-run-substring", default=DEFAULT_RUN_EXPECT, help="Required substring in run output.")
    parser.add_argument("--skip-chat", action="store_true", help="Skip /v1/chat/completions probe.")
    parser.add_argument("--skip-runs", action="store_true", help="Skip /v1/runs + SSE probe.")
    parser.add_argument("--keep-home", action="store_true", help="Do not delete the temporary HERMES_HOME.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    port = args.port or find_free_port()

    temp_home = Path(tempfile.mkdtemp(prefix="hermes-gw-smoke-"))
    log_path = temp_home / "gateway.log"
    try:
        copy_runtime_config(args.source_home, temp_home)
        env = build_gateway_env(temp_home, args.workspace.resolve(), port, args.api_key)
        proc = start_gateway(log_path, env)
        try:
            health = wait_for_health(f"http://127.0.0.1:{port}", timeout=args.startup_timeout)
            print(f"base_url=http://127.0.0.1:{port}")
            print(f"temp_home={temp_home}")
            print(f"health_status={health.get('status')}")

            if not args.skip_chat:
                chat_response, session_id = run_chat_probe(
                    f"http://127.0.0.1:{port}",
                    args.api_key,
                    args.chat_prompt,
                    timeout=args.request_timeout,
                )
                chat_text = extract_chat_text(chat_response)
                if args.expect_chat_substring not in chat_text:
                    raise RuntimeError(
                        f"Chat output missing expected substring {args.expect_chat_substring!r}: {chat_text!r}"
                    )
                print(f"chat_status={chat_response.status_code}")
                print(f"chat_session_id={session_id}")
                print(f"chat_text={chat_text}")

            if not args.skip_runs:
                run_id, events = run_async_probe(
                    f"http://127.0.0.1:{port}",
                    args.api_key,
                    args.run_prompt,
                    timeout=args.request_timeout,
                )
                event_names = ",".join(event["event"] for event in events)
                final_output = collect_final_output(events)
                if args.expect_run_substring not in final_output:
                    raise RuntimeError(
                        f"Run output missing expected substring {args.expect_run_substring!r}: {final_output!r}"
                    )
                print("runs_status=202")
                print(f"run_id={run_id}")
                print(f"sse_event_count={len(events)}")
                print(f"sse_events={event_names}")
                print(f"run_final_output={final_output}")
        finally:
            stop_gateway(proc)
    except Exception as exc:
        print(f"smoke_status=failed")
        print(f"error={exc}")
        tail = _tail_text(log_path)
        if tail:
            print("gateway_log_tail<<EOF")
            print(tail)
            print("EOF")
        return 1
    finally:
        if args.keep_home:
            print(f"kept_temp_home={temp_home}")
        else:
            shutil.rmtree(temp_home, ignore_errors=True)

    print("smoke_status=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
