"""Native SuperTux camera and first-coin referee; no private state in observations."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


class SuperTuxPixelsEnv:
    engine_version = "0.6.3+ggbench1"
    actions = [
        "wait",
        "left",
        "right",
        "jump",
        "jump_left",
        "jump_right",
        "run_right",
        "run_jump_right",
        "duck",
    ]

    def __init__(self, seed):
        self.scratch = tempfile.TemporaryDirectory(prefix="ggbench-supertux-")
        self.directory = Path(self.scratch.name)
        self.log = tempfile.TemporaryFile()
        self.process = None
        self.done, self.coins = False, 0
        try:
            self.process = subprocess.Popen(
                [
                    "/source/build/supertux2",
                    "--datadir",
                    "/source/data",
                    "--userdir",
                    self.scratch.name,
                    "--renderer",
                    "sdl",
                    "--geometry",
                    "640x480",
                    "--disable-sound",
                    "--disable-music",
                    "--no-show-fps",
                    "--no-show-pos",
                    "/source/data/levels/world1/welcome_antarctica.stl",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self.log,
                text=True,
                env={
                    **os.environ,
                    "HOME": self.scratch.name,
                    "GGBENCH_CAPTURE": str(self.directory / "camera.bmp"),
                    "GGBENCH_SEED": str(seed),
                    "LC_ALL": "C.UTF-8",
                },
            )
            self.initial = self._read()
        except BaseException:
            self.close()
            raise

    def _read(self):
        # Native engine logging may precede its explicit referee record.
        while True:
            line = self.process.stdout.readline()
            if not line:
                self.log.seek(0)
                raise RuntimeError(
                    "SuperTux exited: " + self.log.read().decode(errors="replace")[-1500:]
                )
            if line.startswith("GGBENCH "):
                state = json.loads(line[8:])
                self.coins, self.done = int(state["coins"]), bool(state["done"])
                with Image.open(self.directory / "camera.bmp") as image:
                    if image.size != (640, 480):
                        raise ValueError("Unexpected SuperTux camera dimensions")
                    return np.array(image.convert("RGB"))

    def reset(self):
        return self.initial.copy()

    def step(self, action):
        if self.done or type(action) is not int or not 0 <= action < len(self.actions):
            raise ValueError("Illegal SuperTux action or finished episode")
        previous = self.coins
        self.process.stdin.write(str(action) + "\n")
        self.process.stdin.flush()
        image = self._read()
        return image, float(self.coins - previous), self.done, False, {}

    def close(self):
        try:
            if self.process is not None:
                self.process.stdin.close()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait()
                self.process.stdout.close()
                self.process = None
        finally:
            self.log.close()
            self.scratch.cleanup()
