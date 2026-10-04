"""Native OpenTTD mouse/keyboard control and first-road referee."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


class OpenTTDPixelsEnv:
    engine_version = "15.3+ggbench1"
    actions = [
        "wait",
        "cursor_up",
        "cursor_right",
        "cursor_down",
        "cursor_left",
        "left_press",
        "left_release",
        "road_toolbar",
        "autoroad",
        "cancel",
    ]

    def __init__(self, seed):
        self.scratch = tempfile.TemporaryDirectory(prefix="ggbench-openttd-")
        self.directory = Path(self.scratch.name)
        self.log = tempfile.TemporaryFile()
        self.process = None
        self.done, self.roads = False, 0
        config = self.directory / "config.ini"
        config.write_text(
            "[misc]\nfullscreen = false\nresolution = 800, 600\nlanguage = english.lng\n"
            "videodriver = null\nsounddriver = null\nmusicdriver = null\n"
            "[game_creation]\nmap_x = 6\nmap_y = 6\nstarting_year = 1950\nland_generator = 1\n"
            "[ai]\nmax_no_competitors = 0\n[difficulty]\nnumber_towns = 0\n"
            "[gui]\nautosave = off\nautosave_on_exit = false\nshow_finances = false\n"
        )
        try:
            self.process = subprocess.Popen(
                [
                    "/source/build/openttd",
                    "-c",
                    str(config),
                    "-v",
                    "null",
                    "-s",
                    "null",
                    "-m",
                    "null",
                    "-r",
                    "800x600",
                    "-g",
                    "-G",
                    str(seed),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self.log,
                text=True,
                env={
                    **os.environ,
                    "HOME": self.scratch.name,
                    "GGBENCH_CAPTURE": str(self.directory / "camera.ppm"),
                    "LC_ALL": "C.UTF-8",
                },
            )
            self.initial = self._read()
        except BaseException:
            self.close()
            raise

    def _read(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                self.log.seek(0)
                raise RuntimeError(
                    "OpenTTD exited: " + self.log.read().decode(errors="replace")[-1500:]
                )
            if line.startswith("GGBENCH "):
                state = json.loads(line[8:])
                if not state["ready"]:
                    raise RuntimeError("OpenTTD did not create the player company")
                self.roads = int(state["roads"])
                self.done = self.roads >= 2
                with Image.open(self.directory / "camera.ppm") as image:
                    if image.size != (800, 600):
                        raise ValueError("Unexpected OpenTTD camera dimensions")
                    return np.array(image.convert("RGB"))

    def reset(self):
        return self.initial.copy()

    def step(self, action):
        if self.done or type(action) is not int or not 0 <= action < len(self.actions):
            raise ValueError("Illegal OpenTTD action or finished episode")
        self.process.stdin.write(str(action) + "\n")
        self.process.stdin.flush()
        image = self._read()
        return image, float(self.done), self.done, False, {}

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
