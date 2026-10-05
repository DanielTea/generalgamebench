"""Portable exports must preserve provenance and never mix trust tracks."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "export_huggingface", Path(__file__).parents[1] / "scripts/export_huggingface.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_export_preserves_task_model_seed_and_trust(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text('<script src="app.js"></script>')
    ranking = {
        "agent": "vision",
        "model": "provider/model",
        "mode": "exhibition",
        "score": 25,
        "per_game": {"maze": 25},
        "games": ["maze"],
        "seeds": 1,
        "seed_ids": [71],
        "max_steps": 8,
        "latency_eligible": False,
        "p95_ms": 3000,
        "max_ms": 4000,
        "trust": "local-unattested",
        "hardware": "test",
        "version": "0.2.0",
        "task_metadata": {"maze": {"task_version": "1", "engine_version": "3"}},
        "provider_metadata": {"revision": "weights-sha", "prompt_version": "v2"},
    }
    (site / "data.json").write_text(
        json.dumps(
            {
                "season": "0.2",
                "exhibition": [ranking],
                "official": [],
                "hardware_details": "M3 Max; concurrent",
            }
        )
    )
    out = tmp_path / "export"
    module.export(site, out)
    row = json.loads((out / "dataset/exhibition.jsonl").read_text())
    assert row["seed_ids"] == [71]
    assert row["model_revision"] == "weights-sha"
    assert row["task_metadata"]["engine_version"] == "3"
    assert row["trust"] == "local-unattested"
    assert row["hardware_details"] == "M3 Max; concurrent"
    assert len(row["suite_id"]) == 64
    assert len(row["snapshot_sha256"]) == 64
    ranking["task_metadata"]["maze"]["engine_version"] = "different-engine"
    (site / "data.json").write_text(json.dumps({"exhibition": [ranking]}))
    module.export(site, tmp_path / "different")
    changed = json.loads((tmp_path / "different/dataset/exhibition.jsonl").read_text())
    assert changed["suite_id"] != row["suite_id"]
    assert changed["snapshot_sha256"] != row["snapshot_sha256"]
    assert not (out / "dataset/official.jsonl").exists()
    assert "sdk: static" in (out / "space/README.md").read_text()
    assert (out / "space/index.html").read_text() == (site / "index.html").read_text()
    with pytest.raises(FileExistsError):
        module.export(site, out)


def test_archive_preserves_its_own_campaign_metadata(tmp_path):
    site = Path(__file__).parents[1] / "site/dist"
    snapshot = json.loads((site / "data.json").read_text())
    old = snapshot["local"][0]
    minimal = tmp_path / "site"
    minimal.mkdir()
    (minimal / "data.json").write_text(
        json.dumps(
            {
                "season": "refresh",
                "hardware_details": "current workers",
                "exhibition_previous": [old],
                "track_metadata": {
                    "exhibition_previous": {"season": "old", "hardware_details": "previous workers"}
                },
            }
        )
    )
    module.export(minimal, tmp_path / "export")
    rows = (tmp_path / "export/dataset/exhibition_previous.jsonl").read_text().splitlines()
    assert rows
    assert all(json.loads(row)["season"] == "old" for row in rows)
    assert all(json.loads(row)["hardware_details"] == "previous workers" for row in rows)
