"""A provider failure must remain evidence without becoming an aggregate rank."""

import importlib.util
import json
from pathlib import Path

from generalgamebench import __version__
from generalgamebench.models import ProviderUnavailable
from generalgamebench.runner import run_episode


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
