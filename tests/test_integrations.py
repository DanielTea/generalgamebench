"""Real engine contract tests. Enable explicitly after installing game runtimes."""

import io
import os

import pytest
from PIL import Image

from generalgamebench.games import make_game
from generalgamebench.registry import TASKS

pytestmark = pytest.mark.skipif(
    os.environ.get("GGBENCH_RUN_INTEGRATION") != "1",
    reason="Set GGBENCH_RUN_INTEGRATION=1 after installing optional runtimes",
)


@pytest.mark.parametrize("task", list(TASKS))
def test_actual_engine_replay(task):
    frames, actions = [], []
    game = make_game(task, 71, 24)
    try:
        while not game.done:
            frame = game.frame()
            image = Image.open(io.BytesIO(frame))
            assert image.mode == "RGB"
            assert min(image.size) >= 32
            frames.append(frame)
            action = len(frames) % len(game.actions)
            actions.append(action)
            game.step(action)
        result, metadata = game.result(), game.metadata
        assert 0 <= result["score"] <= 1
        assert result["steps"] == len(frames)
        with pytest.raises(ValueError):
            game.step(0)
    finally:
        game.close()
    replay = make_game(task, 71, 24)
    try:
        assert replay.metadata == metadata
        for frame, action in zip(frames, actions):
            assert replay.frame() == frame
            replay.step(action)
        assert replay.done
        assert replay.result() == result
    finally:
        replay.close()


def test_minihack_goal_and_early_termination():
    game = make_game("minihack-room", 71, 40)
    try:
        southeast = game.actions.index("se")
        for _ in range(4):
            game.step(southeast)
        assert game.done
        assert game.result()["raw_score"] == 1
        assert game.result()["steps"] == 4
    finally:
        game.close()


def test_procgen_stops_before_automatic_next_episode():
    game = make_game("procgen-bigfish", 71, 2000)
    try:
        while not game.done:
            game.step(0)
        assert game.result()["steps"] < 2000
        with pytest.raises(ValueError):
            game.step(0)
    finally:
        game.close()
