"""A provider failure must remain evidence without becoming an aggregate rank."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from generalgamebench import __version__
from generalgamebench.models import ProviderUnavailable
from generalgamebench.runner import run_episode


def test_replay_source_revision_requires_provenance_and_exact_hashes(tmp_path, monkeypatch):
    scripts = Path(__file__).parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("refresh_export", scripts / "export_refresh.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    source = tmp_path / "adapter.py"
    source.write_text("offscreen")
    current = hashlib.sha256(source.read_bytes()).hexdigest()
    campaign = {"source_hashes": {"adapter.py": "original"}}
    with pytest.raises(ValueError, match="source changed"):
        module.verify_source(campaign)
    campaign["replay_source_hashes"] = {"adapter.py": current}
    with pytest.raises(ValueError, match="Document source changes"):
        module.verify_source(campaign)
    campaign["source_change_note"] = "Original frames and scores replayed off-screen exactly."
    module.verify_source(campaign)
    assert campaign["source_hashes"] == {"adapter.py": "original"}
    source.write_text("unexpected change")
    with pytest.raises(ValueError, match="source changed"):
        module.verify_source(campaign)
    campaign["replay_source_hashes"] = {}
    with pytest.raises(ValueError, match="exactly the recorded source files"):
        module.verify_source(campaign)


def test_refresh_excludes_incomplete_models_and_preserves_failure(tmp_path, monkeypatch):
    scripts = Path(__file__).parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("refresh_export", scripts / "export_refresh.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)

    def save(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    class Policy:
        def __init__(self, model=None, fail=False):
            self.model, self.fail = model, fail
            self.metadata = {"requested_model": model}

        def act(self, obs, timeout):
            if self.fail:
                raise ProviderUnavailable("Test provider is inaccessible")
            return {"nonce": obs["nonce"], "action": 0}

    for name, model, fail, root in (
        ("openai-working", "working", False, "models"),
        ("openai-inaccessible", "inaccessible", True, "models"),
        ("idle", None, False, "controls"),
    ):
        folder = tmp_path / "runs" / root / name
        run_episode(
            Policy(model, fail), name, "coin-run", 3000, folder / "coin-run-3000", 2, "exhibition"
        )
        if model:
            save(
                folder / "status.json",
                {
                    "model": model,
                    "status": "provider-unavailable" if fail else "complete",
                    "completed": 1,
                },
            )
    report = tmp_path / "results/refresh"
    save(
        report / "campaign.json",
        {
            "id": "refresh",
            "version": __version__,
            "source_hashes": {},
            "games": ["coin-run"],
            "seeds": [3000],
            "max_steps": 2,
            "mode": "exhibition",
            "assignments": {"runs/models": ["working", "inaccessible"]},
            "controls": ["idle"],
            "control_root": "runs/controls",
            "concurrency_note": "current machine",
        },
    )
    save(
        report / "model-inventory.json",
        {
            "models": [
                {"provider": "openai", "model": model} for model in ("working", "inaccessible")
            ]
        },
    )
    save(
        tmp_path / "results/season-0.2/snapshot.json",
        {"exhibition": [{"agent": "old"}], "hardware_details": "original machine"},
    )
    save(tmp_path / "site/dist/data.json", {"coverage": {}, "local": [], "official": []})

    failed_status = tmp_path / "runs/models/openai-inaccessible/status.json"
    prior = json.loads(failed_status.read_text())
    save(failed_status, {**prior, "status": "blocked"})
    with pytest.raises(ValueError, match="Resolve blocked campaign"):
        module.export(report)
    assert not (report / "snapshot.json").exists()
    save(failed_status, prior)
    module.export(report)
    snapshot = json.loads((report / "snapshot.json").read_text())
    assert {row["agent"] for row in snapshot["exhibition"]} == {"openai-working", "idle"}
    assert snapshot["exhibition_previous"] == [{"agent": "old"}]
    assert (
        snapshot["track_metadata"]["exhibition_previous"]["hardware_details"] == "original machine"
    )
    failed = json.loads((report / "incomplete-episodes.json").read_text())
    assert len(failed) == 1 and failed[0]["score"] == 0
    assert failed[0]["errors"] == ["ProviderUnavailable"]
    assert len(json.loads((report / "evidence-roots.json").read_text())) == 3
    assert snapshot["official"] == []
