"""A refreshed baseline board requires complete evidence and preserves other cohorts."""

import importlib.util
import json
from pathlib import Path

import pytest

from generalgamebench import __version__
from generalgamebench.runner import run_episode


def test_complete_baseline_matrix_preserves_history_and_failed_episodes(tmp_path, monkeypatch):
    scripts = Path(__file__).parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location(
        "baseline_export", scripts / "export_baseline_campaign.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)

    def save(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    class Policy:
        def __init__(self, fail=False):
            self.fail = fail

        def act(self, obs, timeout):
            if self.fail:
                raise TimeoutError("Retained failure")
            return {"nonce": obs["nonce"], "action": 0}

    report = tmp_path / "results/baselines"
    campaign = {
        "id": "new-baselines",
        "version": __version__,
        "source_hashes": {},
        "agents": ["idle"],
        "games": ["coin-run"],
        "seeds": [4000, 4001],
        "mode": "realtime",
        "max_steps": 2,
        "run_root": "runs/baselines",
        "suite_file": "benchmarks/new.json",
        "concurrency_note": "serial",
    }
    prior = {
        "season": "old",
        "local": [{"agent": "old-reference"}],
        "exhibition": [{"agent": "model"}],
        "exhibition_previous": [{"agent": "old-model"}],
        "official": [],
        "model_status": [{"status": "complete"}],
        "current_campaign": "cloud/campaign.json",
        "track_metadata": {
            "local": {"season": "old", "hardware_details": "shared"},
            "exhibition": {"season": "cloud", "hardware_details": "concurrent"},
        },
    }
    save(report / "campaign.json", campaign)
    save(report / "run-status.json", {"status": "running", "completed": 0, "expected": 2})
    save(tmp_path / "site/dist/data.json", prior)
    with pytest.raises(ValueError, match="Finish serial recording"):
        module.export(report)
    save(
        report / "run-status.json",
        {"status": "recorded-awaiting-replay", "completed": 2, "expected": 2},
    )
    first = tmp_path / "runs/baselines/idle/coin-run-4000"
    run_episode(Policy(), "idle", "coin-run", 4000, first, 2)
    with pytest.raises(ValueError, match="Missing or extra"):
        module.export(report)
    assert not (report / "snapshot.json").exists()
    second = tmp_path / "runs/baselines/idle/coin-run-4001"
    run_episode(Policy(True), "idle", "coin-run", 4001, second, 2)
    real_result = json.loads((second / "result.json").read_text())
    save(second / "result.json", {**real_result, "score": 1})
    with pytest.raises(ValueError, match="sidecar differs"):
        module.export(report)
    save(second / "result.json", real_result)
    module.export(report, workers=1)
    snapshot = json.loads((report / "snapshot.json").read_text())
    for key in (
        "exhibition",
        "exhibition_previous",
        "official",
        "model_status",
        "current_campaign",
    ):
        assert snapshot[key] == prior[key]
    assert snapshot["local_previous"] == prior["local"]
    assert snapshot["track_metadata"]["local_previous"] == prior["track_metadata"]["local"]
    assert snapshot["track_metadata"]["exhibition"] == prior["track_metadata"]["exhibition"]
    row = snapshot["local"][0]
    assert row["episodes"] == 2 and row["errors"] == 1
    assert not row["latency_eligible"]
    assert len(json.loads((report / "replay-validation.json").read_text())) == 2
    assert json.loads((report / "run-status.json").read_text())["status"] == "replay-verified"
    assert json.loads((report / "episodes.json").read_text())[1]["score"] == 0
    with pytest.raises(FileExistsError):
        module.export(report)
