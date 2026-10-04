"""Bounded JSONL protocol: supervisor timestamps, fresh challenge, one outstanding frame."""

from __future__ import annotations

import json
import os
import selectors
import signal
import subprocess
import time

MAX_REPLY = 4096


class ProtocolError(ValueError):
    pass


def validate_reply(reply: dict, observation: dict) -> int:
    if not isinstance(reply, dict) or set(reply) != {"nonce", "action"}:
        raise ProtocolError("Expected exactly nonce and action")
    if reply["nonce"] != observation["nonce"]:
        raise ProtocolError("Stale or unsolicited action")
    action = reply["action"]
    if type(action) is not int or not 0 <= action < len(observation["actions"]):
        raise ProtocolError("Action is not an allowed integer")
    return action


class ProcessAgent:
    """Development transport, NOT an OS security sandbox. See SECURITY.md."""

    def __init__(self, command: list[str], cwd: str | None = None):
        env = {
            k: v
            for k, v in os.environ.items()
            if k in {"PATH", "SYSTEMROOT", "LANG", "LC_ALL", "PYTHONPATH"}
        }
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=cwd,
            env=env,
            bufsize=0,
            start_new_session=True,
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.buffer = b""
        os.set_blocking(self.process.stdin.fileno(), False)
        try:
            if self._readline(10.0) != {"ready": True}:
                raise ProtocolError("Missing readiness handshake")
        except Exception:
            self.close()
            raise

    def _readline(self, timeout: float) -> dict:
        deadline = time.perf_counter() + timeout
        while b"\n" not in self.buffer:
            remaining = deadline - time.perf_counter()
            if remaining <= 0 or not self.selector.select(remaining):
                raise TimeoutError("Agent response deadline exceeded")
            data = os.read(self.process.stdout.fileno(), MAX_REPLY + 1)
            if not data:
                raise ProtocolError("Agent exited before responding")
            self.buffer += data
            if len(self.buffer) > MAX_REPLY:
                raise ProtocolError("Oversized response")
        line, self.buffer = self.buffer.split(b"\n", 1)
        if self.buffer:
            raise ProtocolError("Multiple unsolicited replies")
        try:
            return json.loads(line)
        except (ValueError, UnicodeError) as exc:
            raise ProtocolError("Invalid JSON") from exc

    def act(self, observation: dict, timeout: float) -> dict:
        deadline = time.perf_counter() + timeout
        data = memoryview(json.dumps(observation, separators=(",", ":")).encode() + b"\n")
        with selectors.DefaultSelector() as writer:
            writer.register(self.process.stdin, selectors.EVENT_WRITE)
            while data:
                remaining = deadline - time.perf_counter()
                if remaining <= 0 or not writer.select(remaining):
                    raise TimeoutError("Agent stopped reading observations")
                try:
                    written = os.write(self.process.stdin.fileno(), data)
                    data = data[written:]
                except BlockingIOError:
                    continue
        return self._readline(max(0.0, deadline - time.perf_counter()))

    def close(self):
        self.selector.close()
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()
