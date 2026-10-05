"""Keep startup inputs separate from scored games and preserve prior results."""

import base64
import copy
import importlib.util
import io
import sys
from pathlib import Path

import pytest
from PIL import Image

SCRIPTS = Path(__file__).parents[1] / "scripts"


def load_script(name):
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


campaign = load_script("run_campaign")
exporter = load_script("export_local_vlms")


def test_warmup_uses_only_three_declared_synthetic_images():
    observations = []

    class Agent:
        def act(self, observation, timeout):
            observations.append(observation)
            assert timeout == 120
            return {"nonce": observation["nonce"], "action": None}

    campaign.warmup_agent(Agent(), campaign.WARMUP_PROFILE)
    assert len({row["nonce"] for row in observations}) == 3
    for row, size in zip(observations, [(160, 120), (320, 240), (960, 640)]):
        frame = Image.open(io.BytesIO(base64.b64decode(row["image_png"])))
        assert frame.size == size
        assert frame.getextrema() == ((128, 128),) * 3
        assert row["instructions"] == "This is a startup check. Choose wait."
        assert row["actions"] == ["wait", "left", "right"]
        assert not ({"seed", "score", "state"} & row.keys())
    with pytest.raises(ValueError, match="Unknown"):
        campaign.warmup_agent(Agent(), "unknown-profile")


def test_append_keeps_existing_rows_and_rejects_mixed_suites():
    old = {
        "agent": "old",
        "score": 10,
        "games": ["coin-run"],
        "seed_ids": [3000],
        "mode": "exhibition",
        "hardware": "Darwin arm64",
        "version": "0.4.0",
        "max_steps": 8,
        "task_metadata": {"coin-run": {}},
    }
    new = {**old, "agent": "new", "score": 20}
    original = {"exhibition": [old], "official": [], "local": [{"agent": "archived"}]}
    result = exporter.append_board(copy.deepcopy(original), [new], [])
    assert result["exhibition"] == [new, old]
    assert result["official"] == original["official"]
    assert result["local"] == original["local"]
    with pytest.raises(ValueError, match="replace"):
        exporter.append_board(copy.deepcopy(original), [old], [])
    with pytest.raises(ValueError, match="same game suite"):
        exporter.append_board(copy.deepcopy(original), [{**new, "seed_ids": [4000]}], [])
