"""Real engine contract tests. Enable explicitly after installing game runtimes."""

import io
import os
import random
import subprocess
import time
from pathlib import Path

import pytest
from PIL import Image

from generalgamebench.games import make_game
from generalgamebench.registry import TASKS

pytestmark = pytest.mark.skipif(
    os.environ.get("GGBENCH_RUN_INTEGRATION") != "1",
    reason="Set GGBENCH_RUN_INTEGRATION=1 after installing optional runtimes",
)


def test_airstriker_never_opens_a_display():
    root = Path(__file__).resolve().parents[1]
    runtime = Path(os.environ.get("GGBENCH_ENV_ROOT", root / ".game-envs")) / "research"
    python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    # Run the real adapter in its pinned runtime. The previous default calls
    # render() on reset/step to open a window; fail before any GUI is created.
    subprocess.run(
        [
            str(python),
            "-c",
            """
from stable_retro.retro_env import RetroEnv
from generalgamebench.environment_worker import Environment
from generalgamebench.registry import task_dict
def reject_display(self):
    raise AssertionError("Airstriker attempted to open a game display")
RetroEnv.render = reject_display
game = Environment(task_dict("retro-airstriker"), 3000, 24)
try:
    for tick in range(24):
        assert game.frame()
        assert game.engine.viewer is None
        game.step(tick % len(game.actions))
    assert game.done
finally:
    game.close()
""",
        ],
        check=True,
        timeout=60,
        env={**os.environ, "PYTHONPATH": str(root / "src")},
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


def test_unity_food_reward_and_replay():
    # A real food collision at decision 178, beyond a no-op smoke test. Replay
    # both the pre-collision camera and rewarded final frame in fresh processes.
    actions = ([1] * 70 + [5] * 15 + [1] * 60 + [6] * 10 + [3] * 25)[:178]
    reference = None
    for _ in range(2):
        game = make_game("unity-food-collector", 2, len(actions))
        try:
            frames = [game.frame()]
            for action in actions:
                game.step(action)
                frames.append(game.frame())
            result = game.result()
            assert game.done
            assert result["raw_score"] == 1
            assert result["score"] == 0.1
            assert result["steps"] == 178
            measured = frames, result, game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
        finally:
            game.close()


def test_football_goal_and_native_termination():
    reference = None
    for _ in range(2):
        game = make_game("football-empty-goal", 71, 400)
        try:
            frames = [game.frame()]
            for tick in range(400):
                game.step(game.actions.index("shoot" if tick % 10 == 0 else "right"))
                frames.append(game.frame())
                if game.done:
                    break
            result = game.result()
            assert game.done
            assert result["raw_score"] == result["score"] == 1
            assert result["steps"] == 17
            measured = frames, result, game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
            with pytest.raises(ValueError):
                game.step(0)
        finally:
            game.close()


def test_luanti_tree_goal_and_replay():
    reference = None
    for _ in range(2):
        game = make_game("luanti-chop-tree", 71, 160)
        try:
            frames = [game.frame()]
            for tick in range(160):
                game.step(4 if tick < 4 else 1 if tick < 24 else 3)
                frames.append(game.frame())
                if game.done:
                    break
            result = game.result()
            assert game.done
            assert result["raw_score"] == result["score"] == 1
            assert result["steps"] == 50
            measured = frames, result, game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
            with pytest.raises(ValueError):
                game.step(0)
        finally:
            game.close()


def test_luanti_scene_updates_replay_over_600_decisions():
    reference = None
    for repeat in range(2):
        game = make_game("luanti-chop-tree", 71, 600)
        try:
            frames = [game.frame()]
            for tick in range(600):
                if repeat and tick % 17 == 0:
                    time.sleep(0.019)
                game.step(1 if tick < 80 else 3)
                frames.append(game.frame())
            assert game.done
            assert game.result()["steps"] == 600
            assert game.result()["raw_score"] == 0
            measured = frames, game.result(), game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
        finally:
            game.close()


@pytest.mark.parametrize("policy, expected_steps, score", [("goal", 12, 1), ("idle", 101, 0)])
def test_supertux_coin_goal_and_native_death_replay(policy, expected_steps, score):
    reference = None
    for repeat in range(2):
        game = make_game("supertux-first-coin", 71, 160)
        try:
            frames = [game.frame()]
            for tick in range(160):
                if repeat and tick % 13 == 0:
                    time.sleep(0.023)
                action = 7 if tick % 10 < 4 else 6
                game.step(0 if policy == "idle" else action)
                frames.append(game.frame())
                if game.done:
                    break
            assert game.done
            assert game.result()["steps"] == expected_steps
            assert game.result()["raw_score"] == game.result()["score"] == score
            measured = frames, game.result(), game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
            with pytest.raises(ValueError):
                game.step(0)
        finally:
            game.close()


def test_supertuxkart_progress_and_replay_despite_variable_agent_delays():
    reference = None
    for repeat in range(2):
        game = make_game("supertuxkart-lighthouse", 71, 200)
        try:
            frames = [game.frame()]
            for tick in range(200):
                if repeat and tick % 11 == 0:
                    time.sleep(0.027)
                game.step(1 if tick % 15 else 2)
                frames.append(game.frame())
            result = game.result()
            assert game.done
            assert result["steps"] == 200
            assert 0.1 < result["score"] < 0.2
            assert 90 < result["metrics"]["distance_m"] < 120
            assert not result["metrics"]["finished"]
            measured = frames, result, game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
        finally:
            game.close()


@pytest.mark.parametrize("steps,repeats", [(200, 3), (50, 12)])
def test_supertuxkart_random_controls_replay_at_seed_5001(tmp_path, steps, repeats):
    # Fresh shader mesh addresses exposed a depth tie at decision 38. Retain
    # the long replay and cover that boundary in more independent processes.
    rng = random.Random(1729)
    actions = [rng.randrange(6) for _ in range(steps)]
    reference = None

    def compare(frame, step):
        if reference is not None and frame != reference[0][step]:
            (tmp_path / f"expected-{step}.png").write_bytes(reference[0][step])
            (tmp_path / f"actual-{repeat}-{step}.png").write_bytes(frame)
            pytest.fail(f"Replay image differs at step {step}, repeat {repeat}.")

    for repeat in range(repeats):
        game = make_game("supertuxkart-lighthouse", 5001, len(actions))
        try:
            frames = [game.frame()]
            compare(frames[0], 0)
            for step, action in enumerate(actions, 1):
                game.step(action)
                frames.append(game.frame())
                compare(frames[-1], step)
            measured = frames, game.result(), game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
        finally:
            game.close()


@pytest.mark.parametrize("action", ["wait", "rescue"])
def test_supertuxkart_start_sentinel_does_not_award_a_lap(action):
    game = make_game("supertuxkart-lighthouse", 71, 24)
    try:
        while not game.done:
            game.step(game.actions.index(action))
        assert game.result()["score"] == 0
        assert not game.result()["metrics"]["finished"]
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


def test_crafter_respawn_is_stable_across_processes():
    # Seed 4001 exposed address-ordered creature selection at the tick-10
    # population rebalance. Extend well beyond that boundary in fresh workers.
    actions = [1, 2, 2, 1, 1, 1, 2, 2, 2, 1, 1] * 12
    reference = None
    for _ in range(4):
        game = make_game("crafter", 4001, len(actions))
        try:
            frames = []
            for action in actions:
                frames.append(game.frame())
                game.step(action)
                if game.done:
                    break
            measured = (frames, game.result())
            assert game.metadata["task_version"] == "2"
            if reference is None:
                reference = measured
            else:
                assert measured == reference
        finally:
            game.close()


@pytest.mark.parametrize("seed,route", [(71, "nlukyhhhbjjjnbhhhhhhbbbb"), (0, "." * 80)])
def test_crawl_goal_and_reserved_zero_seed_replay(seed, route):
    from generalgamebench.crawl_engine import CrawlPixelsEnv

    reference = None
    for trial in range(2):
        game = make_game("dcss-first-experience", seed, len(route))
        try:
            frames = [game.frame()]
            for key in route:
                if game.done:
                    break
                if trial:
                    time.sleep(0.019)
                game.step(CrawlPixelsEnv.keys.index(key))
                frames.append(game.frame())
            assert game.done
            result = game.result()
            if seed == 71:
                assert result["score"] == 1
                assert result["steps"] == 24
            else:
                assert result["steps"] == 80
            measured = frames, result, game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
        finally:
            game.close()


@pytest.mark.parametrize("policy", ["road", "random"])
def test_openttd_native_construction_and_replay(policy):
    rng = random.Random(1729)
    actions = [7, 8, 5, 2, 2, 2, 6] if policy == "road" else [rng.randrange(10) for _ in range(200)]
    reference = None
    for repeat in range(2):
        game = make_game("openttd-first-road", 71, len(actions))
        try:
            frames = [game.frame()]
            for action in actions:
                if game.done:
                    break
                if repeat:
                    time.sleep(0.017)
                game.step(action)
                frames.append(game.frame())
            assert game.done
            result = game.result()
            if policy == "road":
                assert result["score"] == 1
                assert result["steps"] == 7
            measured = frames, result, game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
        finally:
            game.close()


def test_mindustry_native_mining_and_delayed_replay():
    actions = [3] * 4 + [5] * 3 + [0] * 10 + [9] + [0] * 80
    reference = None
    for repeat in range(2):
        game = make_game("mindustry-copper", 71, len(actions))
        try:
            frames = [game.frame()]
            for action in actions:
                if game.done:
                    break
                if repeat:
                    time.sleep(0.019)
                game.step(action)
                frames.append(game.frame())
            assert game.done
            result = game.result()
            assert result["raw_score"] == 15
            assert result["score"] == 1
            assert result["steps"] == 43
            measured = frames, result, game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
        finally:
            game.close()


@pytest.mark.parametrize(
    "task,actions,expected_steps",
    [
        ("cdda-first-weapon", [3, 11] * 22 + [7] * 3 + [12, 13], 49),
        (
            "warzone-first-derrick",
            [4] * 4 + [1] * 2 + [5] + [4] * 4 + [1, 13, 12, 12, 5] + [0] * 40,
            41,
        ),
    ],
)
def test_native_tutorial_goal_and_delayed_replay(task, actions, expected_steps):
    reference = None
    for repeat in range(2):
        game = make_game(task, 71, len(actions))
        try:
            frames = [game.frame()]
            for action in actions:
                if game.done:
                    break
                if repeat:
                    time.sleep(0.019)
                game.step(action)
                frames.append(game.frame())
            assert game.done
            result = game.result()
            assert result["raw_score"] == result["score"] == 1
            assert result["steps"] == expected_steps
            measured = frames, result, game.metadata
            if reference is None:
                reference = measured
            else:
                assert measured == reference
        finally:
            game.close()
