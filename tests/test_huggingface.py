"""Portable exports must preserve provenance and never mix trust tracks."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "export_huggingface", Path(__file__).parents[1] / "scripts/export_huggingface.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

publisher_spec = importlib.util.spec_from_file_location(
    "publish_huggingface", Path(__file__).parents[1] / "scripts/publish_huggingface.py"
)
publisher = importlib.util.module_from_spec(publisher_spec)
publisher_spec.loader.exec_module(publisher)


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


def test_real_snapshot_is_loadable_and_discoverable(tmp_path):
    yaml = pytest.importorskip("yaml")
    load_dataset = pytest.importorskip("datasets").load_dataset
    site = Path(__file__).parents[1] / "site/dist"
    module.export(site, tmp_path / "export")
    root = tmp_path / "export"
    space_card = yaml.safe_load((root / "space/README.md").read_text().split("---")[1])
    assert space_card["sdk"] == "static"
    assert space_card["colorFrom"] in {
        "red",
        "yellow",
        "green",
        "blue",
        "indigo",
        "purple",
        "pink",
        "gray",
    }
    assert {
        "leaderboard",
        "domain:gaming",
        "submission:semiautomatic",
        "judge:function",
        "test:public",
    } <= set(space_card["tags"])
    assert space_card["datasets"] == [module.DATASET_ID]
    dataset_card = yaml.safe_load((root / "dataset/README.md").read_text().split("---")[1])
    snapshot = json.loads((site / "data.json").read_text())
    for config in dataset_card["configs"]:
        track = config["config_name"]
        data = load_dataset(
            "json",
            data_files=str(root / "dataset" / config["data_files"][0]["path"]),
            split="train",
        )
        source = {r["agent"]: r for r in snapshot[track]}
        assert len(data) == sum(len(r["per_game"]) for r in source.values())
        for row in data:
            original = source[row["agent_id"]]
            assert row["score_100"] == original["per_game"][row["game_id"]]
            assert row["suite_score_100"] == original["score"]
            assert json.loads(row["task_metadata_json"]) == original.get("task_metadata", {}).get(
                row["game_id"]
            )
            assert row["trust"] == original["trust"]
    assert "official" not in {c["config_name"] for c in dataset_card["configs"]}
    assert (root / "dataset/snapshot.json").read_bytes() == (site / "data.json").read_bytes()


def test_publication_rejects_changed_export_and_binds_exact_revision(tmp_path):
    site = Path(__file__).parents[1] / "site/dist"
    root = tmp_path / "export"
    module.export(site, root)
    publication = publisher.verify_export(root)
    assert (
        publication["snapshot_sha256"]
        == hashlib.sha256((site / "data.json").read_bytes()).hexdigest()
    )
    revision = "a" * 40
    publication.update(dataset_revision=revision, source_commit="b" * 40)
    bound = publisher.bind_space(root, publication)
    assert f"/resolve/{revision}/snapshot.json" in bound["index.html"].decode()
    assert f"/tree/{revision}" in bound["README.md"].decode()
    assert json.loads(bound["publication.json"])["dataset_revision"] == revision
    (root / "space/data.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        publisher.verify_export(root)


def test_publication_uploads_dataset_before_space_and_records_its_commit(tmp_path):
    from types import SimpleNamespace

    pytest.importorskip("huggingface_hub")
    events = []

    class Hub:
        def create_repo(self, *args, **kwargs):
            pass

        def repo_info(self, *args, **kwargs):
            return SimpleNamespace(private=False)

        def upload_folder(self, **kwargs):
            events.append(kwargs["repo_type"])
            return SimpleNamespace(oid="a" * 40)

        def create_commit(self, **kwargs):
            events.append(kwargs["repo_type"])
            operation = next(
                p for p in kwargs["operations"] if p.path_in_repo == "publication.json"
            )
            assert json.loads(operation.path_or_fileobj)["dataset_revision"] == "a" * 40
            return SimpleNamespace(oid="c" * 40)

    root = tmp_path / "export"
    module.export(Path(__file__).parents[1] / "site/dist", root)
    result = publisher.publish(root, "b" * 40, Hub())
    assert events == ["dataset", "space"]
    assert result["space_revision"] == "c" * 40
    assert publisher.verify_export(root)["snapshot_sha256"] == result["snapshot_sha256"]


@pytest.mark.parametrize("track", ["exhibition_previous", "local_previous"])
def test_archive_preserves_its_own_campaign_metadata(tmp_path, track):
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
                track: [old],
                "track_metadata": {
                    track: {"season": "old", "hardware_details": "previous workers"}
                },
            }
        )
    )
    module.export(minimal, tmp_path / "export")
    rows = (tmp_path / f"export/dataset/{track}.jsonl").read_text().splitlines()
    assert rows
    assert all(json.loads(row)["season"] == "old" for row in rows)
    assert all(json.loads(row)["hardware_details"] == "previous workers" for row in rows)
