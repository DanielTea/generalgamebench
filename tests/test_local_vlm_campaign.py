"""Keep startup inputs separate from scored games and preserve prior results."""

import base64
import copy
import importlib.util
import io
import json
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


def model_cohort():
    declaration = {
        "id": "new",
        "version": "0.5.0",
        "games": ["coin-run"],
        "seeds": [3000],
        "max_steps": 8,
        "timeout_s": 120,
        "hardware_details": "Mac. One model at a time.",
        "suite_file": "benchmarks/new.json",
    }
    new = {
        "agent": "new",
        "model": "test/model",
        "score": 20,
        "games": declaration["games"],
        "seed_ids": [3000],
        "episodes": 1,
        "mode": "exhibition",
        "hardware": "Darwin arm64",
        "version": "0.5.0",
        "max_steps": 8,
        "response_timeout_seconds": 120,
        "task_metadata": {"coin-run": {"task_version": "new"}},
        "hardware_details": declaration["hardware_details"],
        "latency_policy": exporter.policy(),
    }
    status = {"agent": "new", "status": "complete", "completed": 1}
    return declaration, new, status


def test_new_cohort_replaces_old_rows_without_changing_other_tracks():
    declaration, new, status = model_cohort()
    old = {
        **new,
        "agent": "old",
        "version": "0.4.0",
        "task_metadata": {"coin-run": {"task_version": "old"}},
    }
    original = {
        "exhibition": [old],
        "official": [],
        "local": [{"agent": "archived"}],
        "coverage": {},
        "model_status": [{"agent": "old"}],
    }
    result = exporter.replace_board(copy.deepcopy(original), [new], [status], declaration)
    assert result["exhibition"] == [new]
    assert result["model_status"] == [status]
    assert result["official"] == original["official"]
    assert result["local"] == original["local"]
    assert original["exhibition"] == [old]
    assert result["track_metadata"]["exhibition"]["season"] == "new"


@pytest.mark.parametrize(
    "changes",
    [
        {"version": "0.4.0"},
        {"latency_policy": {}},
        {"model": None},
        {"seed_ids": [4000]},
        {"episodes": 0},
        {"response_timeout_seconds": 30},
    ],
)
def test_new_cohort_rejects_invalid_or_incomplete_results(changes):
    declaration, new, status = model_cohort()
    with pytest.raises(ValueError):
        exporter.replace_board({"coverage": {}}, [{**new, **changes}], [status], declaration)


def test_new_cohort_rejects_mixed_tasks_and_incomplete_status():
    declaration, new, status = model_cohort()
    second = {**new, "agent": "second", "task_metadata": {"coin-run": {}}}
    second_status = {**status, "agent": "second"}
    with pytest.raises(ValueError, match="same suite"):
        exporter.replace_board({}, [new, second], [status, second_status], declaration)
    with pytest.raises(ValueError, match="complete"):
        exporter.replace_board({}, [new], [{**status, "completed": 0}], declaration)


def test_export_preserves_the_previous_snapshot_bytes(tmp_path, monkeypatch):
    declaration, new, status = model_cohort()
    entry = {
        "provider": "mlx",
        "model": new["model"],
        "revision": "fixed",
        "warmup": campaign.WARMUP_PROFILE,
    }
    name = campaign.model_id(entry)
    new["agent"] = status["agent"] = name
    declaration.update(run_root="runs/new", mode="exhibition", prompt_version="test/1")
    report = tmp_path / "results/new"
    report.mkdir(parents=True)
    (report / "campaign.json").write_text(json.dumps(declaration))
    (report / "model-inventory.json").write_text(json.dumps({"models": [entry]}))
    folder = tmp_path / declaration["run_root"] / name
    episode = folder / "coin-run-3000"
    episode.mkdir(parents=True)
    (folder / "status.json").write_text(json.dumps(status))
    (episode / "events.jsonl").write_text('{"hash": "fixed-root"}\n')
    site = tmp_path / "site/dist"
    site.mkdir(parents=True)
    previous = b'{ "exhibition": [{"agent":"old"}], "season":"old", "current_campaign":"old.json", "coverage": {} }\n'
    (site / "data.json").write_bytes(previous)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/catalog.json").write_text("[]")
    row = {
        **new,
        "game": "coin-run",
        "seed": 3000,
        "provider_metadata": {
            "requested_model": entry["model"],
            "revision": entry["revision"],
            "warmup": entry["warmup"],
            "prompt_version": declaration["prompt_version"],
        },
    }
    monkeypatch.setattr(exporter, "ROOT", tmp_path)
    monkeypatch.setattr(exporter, "verify_source", lambda _: None)
    monkeypatch.setattr(exporter, "verify_episode", lambda _: {"verified": True})
    monkeypatch.setattr(exporter, "read_ledger", lambda _: [row])
    monkeypatch.setattr(exporter, "summarize", lambda *args: [new])
    exporter.export(report, 1)
    assert (report / "previous-snapshot.json").read_bytes() == previous
    saved = json.loads((site / "data.json").read_text())
    assert saved["exhibition"] == [new]
    assert saved["archives"][-1]["sha256"] == exporter.hashlib.sha256(previous).hexdigest()
    assert (report / "snapshot.json").read_bytes() == (site / "data.json").read_bytes()
    with pytest.raises(FileExistsError):
        exporter.export(report, 1)
