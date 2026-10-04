"""Cataclysm: DDA's native tutorial camera and first-weapon referee."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


class CDDAPixelsEnv:
    engine_version = "0.I-1+ggbench1"
    actions = [
        "wait",
        "north",
        "northeast",
        "east",
        "southeast",
        "south",
        "southwest",
        "west",
        "northwest",
        "confirm",
        "cancel",
        "dismiss",
        "wield",
        "choice_0",
        "choice_1",
        "choice_2",
        "choice_3",
    ]
    keys = ".kulnjbhy\n\x1b w0123"

    def __init__(self, seed):
        self.scratch = tempfile.TemporaryDirectory(prefix="ggbench-cdda-")
        self.directory = Path(self.scratch.name)
        self.log = tempfile.TemporaryFile()
        self.process = None
        self.done, self.wielded = False, False
        config = self.directory / "config"
        config.mkdir()
        values = {
            "TERMINAL_X": "120",
            "TERMINAL_Y": "40",
            "FONT_WIDTH": "8",
            "FONT_HEIGHT": "16",
            "FONT_SIZE": "16",
            "ANIMATIONS": "false",
            "FULLSCREEN": "no",
            "USE_TILES": "true",
            "TILES": "UltimateCataclysm",
            "SOFTWARE_RENDERING": "true",
            "RENDERER": "software",
            "USE_LANG": "en",
            "SIDEBAR_POSITION": "right",
            "AUTO_SAVE": "false",
        }
        (config / "options.json").write_text(
            json.dumps([{"name": key, "value": value} for key, value in values.items()])
        )
        try:
            self.process = subprocess.Popen(
                [
                    "/source/build/src/cataclysm-tiles",
                    "--seed",
                    str(seed),
                    "--userdir",
                    self.scratch.name,
                ],
                cwd="/source",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self.log,
                text=True,
                env={
                    **os.environ,
                    "HOME": self.scratch.name,
                    "GGBENCH_CAPTURE": str(self.directory / "camera.bmp"),
                    "LC_ALL": "C.UTF-8",
                },
            )
            self.initial = self._read()
            if self.done:
                raise RuntimeError("Cataclysm tutorial starts in a terminal state")
        except BaseException:
            self.close()
            raise

    def _read(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                self.log.seek(0)
                raise RuntimeError(
                    "Cataclysm exited: " + self.log.read().decode(errors="replace")[-1500:]
                )
            if line.startswith("GGBENCH "):
                state = json.loads(line[8:])
                if not state["ready"]:
                    raise RuntimeError("Cataclysm did not initialize its native tutorial")
                self.wielded = bool(state["wielded"])
                self.done = self.wielded or bool(state["dead"])
                with Image.open(self.directory / "camera.bmp") as image:
                    if image.size != (960, 640):
                        raise ValueError("Unexpected Cataclysm camera dimensions")
                    return np.array(image.convert("RGB"))

    def reset(self):
        return self.initial.copy()

    def step(self, action):
        if self.done or type(action) is not int or not 0 <= action < len(self.actions):
            raise ValueError("Illegal Cataclysm action or finished episode")
        self.process.stdin.write(str(ord(self.keys[action])) + "\n")
        self.process.stdin.flush()
        image = self._read()
        return image, float(self.wielded), self.done, False, {}

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
