"""Mindustry's native Ground Zero camera, controls and copper counter."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


class MindustryPixelsEnv:
    engine_version = "160.5+ggbench1"
    actions = [
        "wait",
        "move_up",
        "move_right",
        "move_down",
        "move_left",
        "cursor_up",
        "cursor_right",
        "cursor_down",
        "cursor_left",
        "click",
    ]

    def __init__(self, seed):
        self.scratch = tempfile.TemporaryDirectory(prefix="ggbench-mindustry-")
        self.directory = Path(self.scratch.name)
        self.log = tempfile.TemporaryFile()
        self.process = None
        self.done, self.copper = False, 0
        try:
            self.process = subprocess.Popen(
                [
                    "xvfb-run",
                    "-a",
                    "-s",
                    "-screen 0 960x640x24",
                    "java",
                    "-Xmx2g",
                    "-Dnodiscord=true",
                    "-Dmindustry.data.dir=" + str(self.directory / "data"),
                    "-cp",
                    "/control/classes:/engine/Mindustry.jar",
                    "BenchmarkLauncher",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self.log,
                text=True,
                env={
                    **os.environ,
                    "HOME": self.scratch.name,
                    "GGBENCH_CAPTURE": str(self.directory / "camera.png"),
                    "GGBENCH_SEED": str(seed),
                    "LC_ALL": "C.UTF-8",
                },
            )
            self.initial = self._read()
            if self.done:
                raise RuntimeError("Mindustry did not reach its initial living player state")
        except BaseException:
            self.close()
            raise

    def _read(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                self.log.seek(0)
                raise RuntimeError(
                    "Mindustry exited: " + self.log.read().decode(errors="replace")[-1500:]
                )
            if line.startswith("GGBENCH "):
                state = json.loads(line[8:])
                self.copper = int(state["copper"])
                self.done = self.copper >= 15 or bool(state["dead"])
                with Image.open(self.directory / "camera.png") as image:
                    if image.size != (960, 640):
                        raise ValueError("Unexpected Mindustry camera dimensions")
                    return np.array(image.convert("RGB"))

    def reset(self):
        return self.initial.copy()

    def step(self, action):
        if self.done or type(action) is not int or not 0 <= action < len(self.actions):
            raise ValueError("Illegal Mindustry action or finished episode")
        previous = self.copper
        self.process.stdin.write(str(action) + "\n")
        self.process.stdin.flush()
        image = self._read()
        return image, float(self.copper - previous), self.done, False, {}

    def close(self):
        try:
            if self.process is not None:
                self.process.stdin.close()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait()
                self.process.stdout.close()
                self.process = None
        finally:
            self.log.close()
            self.scratch.cleanup()
