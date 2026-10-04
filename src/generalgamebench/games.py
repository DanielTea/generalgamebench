"""Referee-owned games. Observations expose rendered pixels and public controls only."""

from __future__ import annotations

import io
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

NATIVE = ("coin-run", "dodge-lanes")
DOOM = (
    "doom-basic",
    "doom-defend-center",
    "doom-defend-line",
    "doom-take-cover",
    "doom-health",
    "doom-corridor",
    "doom-home",
    "doom-predict",
)
SCENARIOS = dict(
    zip(
        DOOM,
        (
            "basic",
            "defend_the_center",
            "defend_the_line",
            "take_cover",
            "health_gathering",
            "deadly_corridor",
            "my_way_home",
            "predict_position",
        ),
    )
)


def png(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


class NativeGame:
    """Two small original games; neither is advertised as an indie or AAA title."""

    def __init__(self, game_id: str, seed: int, max_steps: int = 80):
        self.id, self.rng, self.max_steps = game_id, random.Random(seed), max_steps
        self.t, self.coins, self.hits, self.done = 0, 0, 0, False
        self.player = [5, 8] if game_id == "dodge-lanes" else [5, 5]
        self.target = [self.rng.randrange(10), self.rng.randrange(8)]
        self.obstacles: list[list[int]] = []
        self.actions = ["wait", "left", "right", "up", "down"]
        self.instructions = (
            "Top-down grid. Cyan square is you. Yellow square is a coin. Collect coins. "
            "Actions move one cell. Screen left/right/up/down."
            if game_id == "coin-run"
            else "Cyan square is you at the bottom. Red blocks fall down one cell per turn. "
            "Avoid them by moving left/right. Survive with few hits. Up/down do nothing."
        )

    def frame(self) -> bytes:
        im = Image.new("RGB", (160, 160), (12, 18, 29))
        d = ImageDraw.Draw(im)
        for x in range(0, 160, 16):
            d.line((x, 0, x, 160), fill=(23, 32, 44))
            d.line((0, x, 160, x), fill=(23, 32, 44))

        def cell(p, color):
            x, y = p
            d.rectangle((x * 16 + 3, y * 16 + 3, x * 16 + 12, y * 16 + 12), fill=color)

        if self.id == "coin-run":
            cell(self.target, (255, 209, 70))
        for p in self.obstacles:
            cell(p, (255, 75, 88))
        cell(self.player, (53, 221, 234))
        return png(im)

    def step(self, action: int) -> None:
        dx, dy = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)][action]
        self.player[0] = max(0, min(9, self.player[0] + dx))
        if self.id == "coin-run":
            self.player[1] = max(0, min(9, self.player[1] + dy))
            if self.player == self.target:
                self.coins += 1
                self.target = [self.rng.randrange(10), self.rng.randrange(10)]
        else:
            for p in self.obstacles:
                p[1] += 1
            self.hits += sum(p == self.player for p in self.obstacles)
            self.obstacles = [p for p in self.obstacles if p[1] < 9]
            # Referee randomness is never transmitted to the agent.
            self.obstacles.append([self.rng.randrange(10), 0])
            if self.t % 3 == 0:
                self.obstacles.append([self.rng.randrange(10), 0])
        self.t += 1
        self.done = self.t >= self.max_steps

    def result(self) -> dict:
        raw = self.coins if self.id == "coin-run" else self.max_steps - self.hits
        score = (
            min(1.0, self.coins / max(1, self.max_steps / 6))
            if self.id == "coin-run"
            else max(0.0, 1 - self.hits / max(1, self.max_steps / 10))
        )
        return {
            "raw_score": raw,
            "score": score,
            "steps": self.t,
            "metrics": {"coins": self.coins, "hits": self.hits},
        }

    def close(self):
        pass


class DoomGame:
    def __init__(self, game_id: str, seed: int, max_steps: int = 80):
        import vizdoom as vzd

        self.id, self.t, self.max_steps, self.done = game_id, 0, max_steps, False
        self.engine = vzd.DoomGame()
        self.engine.load_config(str(Path(vzd.scenarios_path) / f"{SCENARIOS[game_id]}.cfg"))
        self.engine.set_window_visible(False)
        self.engine.set_sound_enabled(False)
        self.engine.set_screen_resolution(vzd.ScreenResolution.RES_160X120)
        self.engine.set_screen_format(vzd.ScreenFormat.RGB24)
        self.engine.set_seed(seed)
        self.engine.set_episode_timeout(max_steps * 4 + 20)
        self.engine.init()
        self.engine.new_episode()
        self.buttons = self.engine.get_available_buttons()
        self.actions = ["wait"] + [b.name.lower() for b in self.buttons]
        # No combinations or arbitrary console commands are accepted.
        self.instructions = (
            "First-person Doom scenario. Use the image only. "
            "Each action applies for four game tics. "
            + (
                "Find the exit."
                if game_id == "doom-home"
                else "Collect health and survive."
                if game_id == "doom-health"
                else "Avoid incoming projectiles and survive."
                if game_id == "doom-take-cover"
                else "Aim at monsters and attack; survive and earn scenario reward."
            )
        )
        self.last_frame = None

    def frame(self) -> bytes:
        state = self.engine.get_state()
        if state is not None:
            self.last_frame = png(Image.fromarray(np.asarray(state.screen_buffer)))
        return self.last_frame

    def step(self, action: int) -> None:
        buttons = [False] * len(self.buttons)
        if action:
            buttons[action - 1] = True
        self.engine.make_action(buttons, 4)
        self.t += 1
        self.done = self.engine.is_episode_finished() or self.t >= self.max_steps

    def result(self) -> dict:
        raw = self.engine.get_total_reward()
        # Fixed versioned ranges, NOT per-submission min/max normalization.
        ranges = {
            "doom-basic": (-320, 100),
            "doom-defend-center": (-1, 20),
            "doom-defend-line": (-1, 20),
            "doom-take-cover": (0, self.max_steps * 4),
            "doom-health": (0, self.max_steps * 4),
            "doom-corridor": (-100, 1000),
            "doom-home": (0, 1),
            "doom-predict": (-320, 100),
        }
        lo, hi = ranges[self.id]
        return {
            "raw_score": raw,
            "score": max(0.0, min(1.0, (raw - lo) / (hi - lo))),
            "steps": self.t,
            "metrics": {"normalization": [lo, hi]},
        }

    def close(self):
        self.engine.close()


def make_game(game_id: str, seed: int, max_steps: int = 80):
    if type(seed) is not int or not 0 <= seed < 2**31 or max_steps < 1:
        raise ValueError("Use a nonnegative 31-bit seed and a positive horizon")
    if game_id in NATIVE:
        return NativeGame(game_id, seed, max_steps)
    if game_id in DOOM:
        return DoomGame(game_id, seed, max_steps)
    from .registry import TASKS

    if game_id in TASKS:
        from .worker_game import WorkerGame

        return WorkerGame(game_id, seed, max_steps)
    raise ValueError(f"Unknown game {game_id!r}; use arena games")
