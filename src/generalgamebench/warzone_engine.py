"""Warzone 2100's native tutorial camera, controls and construction counter."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


class WarzonePixelsEnv:
    engine_version = "4.7.0+ggbench1"
    actions = [
        "wait",
        "cursor_up",
        "cursor_right",
        "cursor_down",
        "cursor_left",
        "left_click",
        "right_click",
        "cancel",
        "build_menu",
        "confirm",
        "cursor_up_fine",
        "cursor_right_fine",
        "cursor_down_fine",
        "cursor_left_fine",
    ]

    def __init__(self, seed):
        self.scratch = tempfile.TemporaryDirectory(prefix="ggbench-warzone-")
        self.directory = Path(self.scratch.name)
        self.log = tempfile.TemporaryFile()
        self.process = None
        self.done, self.built = False, 0
        try:
            self.process = subprocess.Popen(
                [
                    "xvfb-run",
                    "-a",
                    "-s",
                    "-screen 0 960x640x24",
                    "/source/build/src/warzone2100",
                    "--game=TUTORIAL3",
                    "--resolution=960x640",
                    "--window",
                    "--noshadows",
                    "--nosound",
                    "--gfxbackend=opengl",
                    "--configdir=" + self.scratch.name,
                ],
                cwd="/source",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self.log,
                text=True,
                env={
                    **os.environ,
                    "HOME": self.scratch.name,
                    "GGBENCH_CAPTURE": str(self.directory / "camera.ppm"),
                    "GGBENCH_SEED": str(seed),
                    "LC_ALL": "C.UTF-8",
                },
            )
            self.initial = self._read()
            if self.done:
                raise RuntimeError("Warzone tutorial starts in a terminal state")
        except BaseException:
            self.close()
            raise

    def _read(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                self.log.seek(0)
                raise RuntimeError(
                    "Warzone exited: " + self.log.read().decode(errors="replace")[-1500:]
                )
            if line.startswith("GGBENCH "):
                state = json.loads(line[8:])
                self.built = int(state["built"])
                self.done = self.built > 0 or int(state["lost"]) >= 2
                with Image.open(self.directory / "camera.ppm") as image:
                    if image.size != (960, 640):
                        raise ValueError("Unexpected Warzone camera dimensions")
                    return np.array(image.convert("RGB"))

    def reset(self):
        return self.initial.copy()

    def step(self, action):
        if self.done or type(action) is not int or not 0 <= action < len(self.actions):
            raise ValueError("Illegal Warzone action or finished episode")
        self.process.stdin.write(str(action) + "\n")
        self.process.stdin.flush()
        image = self._read()
        return image, float(self.built > 0), self.done, False, {}

    def close(self):
        try:
            if self.process is not None:
                self.process.stdin.close()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                self.process.stdout.close()
                self.process = None
        finally:
            self.log.close()
            self.scratch.cleanup()
