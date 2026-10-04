import base64

import pytest

from generalgamebench.baselines import PixelPolicy
from generalgamebench.games import DOOM, NATIVE, make_game


@pytest.mark.parametrize("game_id", NATIVE)
def test_native_reproducibility(game_id):
    a, b = make_game(game_id, 71, 40), make_game(game_id, 71, 40)
    for i in range(40):
        assert a.frame() == b.frame()
        a.step(i % 5)
        b.step(i % 5)
    assert a.result() == b.result()
    assert a.done
    assert 0 <= a.result()["score"] <= 1


def test_visual_policy_collects_coins():
    game = make_game("coin-run", 42, 80)
    policy = PixelPolicy("react")
    for _ in range(80):
        action = policy.act(
            {"image_png": base64.b64encode(game.frame()).decode(), "actions": game.actions}
        )
        game.step(action)
    assert game.coins >= 7


@pytest.mark.parametrize("game_id", DOOM)
def test_doom_adapter_and_replay(game_id):
    pytest.importorskip("vizdoom")
    a = make_game(game_id, 13, 3)
    images = []
    try:
        for _ in range(3):
            images.append(a.frame())
            a.step(0)
        expected = a.result()
    finally:
        a.close()
    b = make_game(game_id, 13, 3)
    try:
        for image in images:
            assert b.frame() == image
            b.step(0)
        assert b.result() == expected
    finally:
        b.close()
