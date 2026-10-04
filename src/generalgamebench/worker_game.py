"""Supervised referee process for incompatible upstream Python environments.

This isolates dependencies, not hostile code. The agent receives no worker handle.
"""

import base64
import json
import os
import selectors
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from .registry import EXPERIMENTAL_TASKS, TASKS, task_dict


class WorkerGame:
    def __init__(self, game_id, seed, max_steps):
        self.id = game_id
        task = (TASKS | EXPERIMENTAL_TASKS)[game_id]
        root = Path(__file__).resolve().parents[2]
        home = Path(os.environ.get("GGBENCH_ENV_ROOT", root / ".game-envs"))
        python = home / task.runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not python.is_file():
            raise RuntimeError(f"Install the {task.runtime} runtime; see environments/README.md")
        self.log = tempfile.TemporaryFile()
        self.process = subprocess.Popen(
            [str(python), "-u", str(Path(__file__).with_name("environment_worker.py"))],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.log,
            bufsize=0,
            start_new_session=True,
            env={
                **os.environ,
                "PYTHONHASHSEED": "0",
                "SDL_AUDIODRIVER": "dummy",
                **({"SDL_VIDEODRIVER": "dummy"} if game_id == "pettingzoo-pistonball" else {}),
            },
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.buffer = b""
        try:
            response = self._call(
                {
                    "command": "init",
                    "task": task_dict(game_id),
                    "seed": seed,
                    "max_steps": max_steps,
                },
                180,
            )
            self.actions = response["actions"]
            self.instructions = response["instructions"]
            self.metadata = response["metadata"]
            self.done = False
        except BaseException:
            self.close()
            raise

    def _call(self, value, timeout=30):
        self.process.stdin.write(json.dumps(value).encode() + b"\n")
        deadline = time.monotonic() + timeout
        while b"\n" not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise TimeoutError("Game worker deadline exceeded")
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                self.log.seek(0)
                detail = self.log.read().decode(errors="replace")[-1500:]
                raise RuntimeError(f"Game worker exited: {detail}")
            self.buffer += chunk
            if len(self.buffer) > 16 * 1024 * 1024:
                raise ValueError("Game worker response too large")
        line, self.buffer = self.buffer.split(b"\n", 1)
        response = json.loads(line)
        if "error" in response:
            raise RuntimeError(response["error"])
        return response

    def frame(self):
        return base64.b64decode(self._call({"command": "frame"})["png"], validate=True)

    def step(self, action):
        if type(action) is not int or not 0 <= action < len(self.actions):
            raise ValueError("Illegal game action")
        if self.done:
            raise ValueError("Episode already finished")
        self.done = self._call({"command": "step", "action": action})["done"]

    def result(self):
        return self._call({"command": "result"})

    def close(self):
        if self.process.poll() is None:
            try:
                self._call({"command": "close"}, 2)
                self.process.wait(timeout=2)
            except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.TimeoutExpired):
                os.killpg(self.process.pid, signal.SIGTERM)
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait()
        self.selector.close()
        self.process.stdin.close()
        self.process.stdout.close()
        self.log.close()
