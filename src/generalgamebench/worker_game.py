"""Supervised referee process for incompatible upstream Python environments.

This isolates dependencies, not hostile code. The agent receives no worker handle.
"""

import base64
import json
import os
import platform
import selectors
import shutil
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
        self.container_cleanup = None
        runtime_metadata = {}
        if task.runtime.startswith("docker-"):
            from .container_runtime import container_command

            command, runtime_metadata, self.container_cleanup = container_command(task.runtime)
        elif not python.is_file():
            raise RuntimeError(f"Install the {task.runtime} runtime; see environments/README.md")
        else:
            command = [str(python), "-u", str(Path(__file__).with_name("environment_worker.py"))]
            if platform.system() == "Linux" and game_id in {
                "unity-food-collector",
                "miniworld-oneroom",
                "retro-airstriker",
            }:
                xvfb = shutil.which("xvfb-run")
                if not xvfb:
                    raise RuntimeError("Install xvfb and xauth for off-screen Linux rendering.")
                command = [xvfb, "-a", "-s", "-screen 0 1280x720x24", *command]
        self.log = tempfile.TemporaryFile()
        private_reply = platform.system() == "Linux" and not task.runtime.startswith("docker-")
        reader, writer = os.pipe() if private_reply else (None, None)
        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=self.log if private_reply else subprocess.PIPE,
                stderr=self.log,
                bufsize=0,
                start_new_session=True,
                pass_fds=(writer,) if private_reply else (),
                env={
                    **{
                        key: value
                        for key, value in os.environ.items()
                        if key != "GGBENCH_WORKER_REPLY_FD"
                    },
                    **({"GGBENCH_WORKER_REPLY_FD": str(writer)} if private_reply else {}),
                    "PYTHONHASHSEED": "0",
                    "SDL_AUDIODRIVER": "dummy",
                    **(
                        {"LIBGL_ALWAYS_SOFTWARE": "1", "LP_NUM_THREADS": "1"}
                        if platform.system() == "Linux"
                        else {}
                    ),
                    **({"SDL_VIDEODRIVER": "dummy"} if game_id == "pettingzoo-pistonball" else {}),
                },
            )
        except BaseException:
            if reader is not None:
                os.close(reader)
            self.log.close()
            raise
        finally:
            if writer is not None:
                os.close(writer)
        self.reply_stream = (
            os.fdopen(reader, "rb", buffering=0) if private_reply else self.process.stdout
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.reply_stream, selectors.EVENT_READ)
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
            self.metadata = {**response["metadata"], **runtime_metadata}
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
            chunk = os.read(self.reply_stream.fileno(), 65536)
            if not chunk:
                self.log.seek(0)
                detail = self.log.read().decode(errors="replace")[-1500:]
                raise RuntimeError(f"Game worker exited: {detail}")
            self.buffer += chunk
            if len(self.buffer) > 16 * 1024 * 1024:
                raise ValueError("Game worker response too large")
        line, self.buffer = self.buffer.split(b"\n", 1)
        try:
            response = json.loads(line)
        except (ValueError, UnicodeError) as exc:
            self.log.seek(0)
            detail = self.log.read().decode(errors="replace")[-1500:]
            raise RuntimeError(f"Invalid game worker reply: {line[:200]!r}; {detail}") from exc
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
                # Docker's Mac client may change its process group. Stop the
                # owned container first; never signal an unrelated group.
                self._remove_container()
                self._signal_worker(signal.SIGTERM)
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self._signal_worker(signal.SIGKILL)
            self.process.wait()
        self.selector.close()
        self.process.stdin.close()
        self.reply_stream.close()
        self.log.close()
        self._remove_container()

    def _signal_worker(self, sig):
        if self.process.poll() is not None:
            return
        try:
            if os.getpgid(self.process.pid) == self.process.pid:
                os.killpg(self.process.pid, sig)
            else:
                self.process.send_signal(sig)
        except (ProcessLookupError, PermissionError):
            # A child can exit between poll/getpgid/kill. Popen checks its own
            # child status again before sending a signal to the exact PID.
            self.process.send_signal(sig)

    def _remove_container(self):
        if self.container_cleanup:
            try:
                subprocess.run(self.container_cleanup, capture_output=True, timeout=15, check=False)
            except (OSError, subprocess.SubprocessError):
                # A stopped/unreachable Docker daemon must not mask the original
                # referee failure. --rm also cleans up on normal container exit.
                pass
