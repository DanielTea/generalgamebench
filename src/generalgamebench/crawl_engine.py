"""DCSS's native tile camera and first-experience referee."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


class CrawlPixelsEnv:
    engine_version = "0.34.0+ggbench1"
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
    ]
    keys = ".kulnjbhy\r\x1b"

    def __init__(self, seed):
        self.scratch = tempfile.TemporaryDirectory(prefix="ggbench-crawl-")
        self.directory = Path(self.scratch.name)
        self.log = tempfile.TemporaryFile()
        self.process = None
        self.done, self.experience, self.hp = False, 0, 0
        # Upstream zero means an unseeded game. Reserve its uint64 maximum for
        # benchmark seed zero, preserving every other benchmark seed verbatim.
        native_seed = seed if seed else 18446744073709551615
        config = self.directory / "init.txt"
        config.write_text(
            "name = GGBench\nspecies = Minotaur\nbackground = Fighter\nweapon = war axe\n"
            f"type = seeded\ngame_seed = {native_seed}\n"
            "remember_name = false\nrestart_after_game = false\nrestart_after_save = false\n"
            "show_more = false\nshow_game_time = false\ntile_full_screen = false\n"
            "tile_window_width = 800\ntile_window_height = 600\ntile_realtime_anim = false\n"
            "tile_water_anim = false\ntile_misc_anim = false\n"
            f"save_dir = {self.directory / 'saves'}\nmorgue_dir = {self.directory / 'morgue'}\n"
        )
        try:
            self.process = subprocess.Popen(
                [
                    "/source/crawl-ref/source/crawl",
                    "-rc",
                    str(config),
                    "-dir",
                    "/source/crawl-ref/source/",
                    "-name",
                    "GGBench",
                    "-seed",
                    str(native_seed),
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
            for _ in range(5):
                self.initial = self._read()
                if self.hp > 0:
                    self.done = False
                    break
                self._key(13)
            else:
                raise RuntimeError("DCSS did not reach its initial player turn")
        except BaseException:
            self.close()
            raise

    def _key(self, key):
        self.process.stdin.write(str(key) + "\n")
        self.process.stdin.flush()

    def _read(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                self.log.seek(0)
                raise RuntimeError(
                    "DCSS exited: " + self.log.read().decode(errors="replace")[-1500:]
                )
            if line.startswith("GGBENCH "):
                state = json.loads(line[8:])
                self.experience, self.hp = int(state["xp"]), int(state["hp"])
                self.done = self.experience > 0 or self.hp <= 0
                with Image.open(self.directory / "camera.ppm") as image:
                    if image.size != (800, 600):
                        raise ValueError("Unexpected DCSS camera dimensions")
                    return np.array(image.convert("RGB"))

    def reset(self):
        return self.initial.copy()

    def step(self, action):
        if self.done or type(action) is not int or not 0 <= action < len(self.actions):
            raise ValueError("Illegal DCSS action or finished episode")
        self._key(ord(self.keys[action]))
        image = self._read()
        return image, float(self.experience > 0), self.done, False, {}

    def close(self):
        try:
            if self.process is not None:
                self.process.stdin.close()
                try:
                    self.process.wait(timeout=1)
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
