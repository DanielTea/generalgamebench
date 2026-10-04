import sys
import time

import pytest

from screenquest_arena.protocol import ProcessAgent, ProtocolError, validate_reply

OBS = {"nonce": "fresh", "actions": ["wait", "left"], "image_png": ""}


@pytest.mark.parametrize(
    "reply",
    [
        None,
        [],
        {},
        {"nonce": "fresh", "action": True},
        {"nonce": "fresh", "action": -1},
        {"nonce": "fresh", "action": 2},
        {"nonce": "old", "action": 0},
        {"nonce": "fresh", "action": 0, "reward": 999},
        {"nonce": "fresh", "action": 0.0},
    ],
)
def test_bad_actions_rejected(reply):
    with pytest.raises(ProtocolError):
        validate_reply(reply, OBS)


def test_valid_action():
    assert validate_reply({"nonce": "fresh", "action": 1}, OBS) == 1


def process(script):
    return ProcessAgent([sys.executable, "-u", "-c", script])


def test_roundtrip_and_secret_scrubbing(monkeypatch):
    monkeypatch.setenv("ARENA_TEST_SECRET", "do-not-inherit")
    agent = process(
        'import os,json,sys; assert "ARENA_TEST_SECRET" not in os.environ; print(json.dumps({"ready":True})); o=json.loads(input()); print(json.dumps({"nonce":o["nonce"],"action":1}))'
    )
    try:
        assert validate_reply(agent.act(OBS, 0.5), OBS) == 1
    finally:
        agent.close()


@pytest.mark.parametrize(
    "payload",
    ["x" * 5000, "not-json", '{"nonce":"fresh","action":0}\n{"nonce":"fresh","action":1}'],
)
def test_bad_wire_reply(payload):
    agent = process(
        f'import json; print(json.dumps({{"ready":True}})); input(); print({payload!r})'
    )
    try:
        with pytest.raises(ProtocolError):
            agent.act(OBS, 0.5)
    finally:
        agent.close()


def test_deadline_and_child_cleanup():
    agent = process('import json,time; print(json.dumps({"ready":True})); input(); time.sleep(10)')
    start = time.perf_counter()
    try:
        with pytest.raises(TimeoutError):
            agent.act(OBS, 0.025)
        assert time.perf_counter() - start < 0.5
    finally:
        agent.close()
    assert agent.process.poll() is not None


def test_nonreader_cannot_block_supervisor():
    agent = process('import json,time; print(json.dumps({"ready":True})); time.sleep(10)')
    start = time.perf_counter()
    try:
        with pytest.raises(TimeoutError):
            agent.act(dict(OBS, image_png="x" * 2_000_000), 0.03)
        assert time.perf_counter() - start < 0.5
    finally:
        agent.close()


def test_bad_handshake():
    with pytest.raises(ProtocolError):
        process('print("{}")')
