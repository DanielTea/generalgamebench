import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def exporter(monkeypatch):
    scripts = Path(__file__).parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("jev_export", scripts / "export_jev.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_container_id_change_requires_exact_trace_proof_and_preserves_metadata(exporter):
    original = {"task": {"container_image": "sha256:old", "engine_revision": "pinned"}}
    current = {"task": {"container_image": "sha256:new", "engine_revision": "pinned"}}
    preserved = copy.deepcopy((original, current))
    with pytest.raises(ValueError, match="rebuild replay audit"):
        exporter.compare_tasks(original, current, {})
    proof = {
        "task": {
            "original_metadata": original["task"],
            "rebuilt_metadata": current["task"],
            "exact_frames": 8,
            "exact_native_score": True,
        }
    }
    exporter.compare_tasks(original, current, proof)
    assert (original, current) == preserved
    current["task"]["engine_revision"] = "different-source"
    with pytest.raises(ValueError, match="rebuild replay audit"):
        exporter.compare_tasks(original, current, proof)


def test_jev_export_refuses_to_replace_existing_snapshot(exporter, tmp_path):
    (tmp_path / "previous-snapshot.json").write_text("original")
    with pytest.raises(FileExistsError):
        exporter.export(tmp_path)
    assert (tmp_path / "previous-snapshot.json").read_text() == "original"


def test_export_replays_failed_suite_and_keeps_previous_rows(exporter, tmp_path, monkeypatch):
    from export_hosted_rerun import __dict__ as base_globals

    from generalgamebench.evidence import verify_episode
    from generalgamebench.jev import ACTION_SCHEMA, IMAGE_PREPROCESSING, TRANSPORT
    from generalgamebench.model_prompt import PROMPT_VERSION
    from generalgamebench.protocol import ProtocolError
    from generalgamebench.ranking import summarize
    from generalgamebench.runner import run_episode

    monkeypatch.setattr(exporter, "ROOT", tmp_path)
    monkeypatch.setitem(base_globals, "ROOT", tmp_path)

    def save(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n")

    def head(path):
        return json.loads((path / "events.jsonl").read_text().splitlines()[-1])["hash"]

    class Agent:
        model = "previous-model"
        metadata = {"prompt_version": PROMPT_VERSION, "transport": "previous"}

        def act(self, obs, timeout):
            return {"nonce": obs["nonce"], "action": 0}

    base_path = tmp_path / "runs/base/coin-run-3000"
    old = run_episode(Agent(), "previous", "coin-run", 3000, base_path, 2, "exhibition", 120)
    old_board = summarize([old], ["coin-run"], [3000])
    old_board[0]["hardware_details"] = "Original run conditions."
    snapshot = {
        "exhibition": old_board,
        "official": [],
        "model_status": [],
        "season": "base",
        "campaigns": [],
        "suite_files": [],
        "track_metadata": {},
        "archives": [],
    }
    base = tmp_path / "results/base"
    relative = str(base_path.relative_to(tmp_path))
    for name, value in {
        "campaign.json": {"source_hashes": {}},
        "snapshot.json": snapshot,
        "episodes.json": [old],
        "evidence-roots.json": {relative: head(base_path)},
        "replay-validation.json": {relative: verify_episode(base_path)},
    }.items():
        save(base / name, value)
    site = tmp_path / "site/dist/data.json"
    save(site, snapshot)
    previous = site.read_bytes()
    report = tmp_path / "results/jev"
    audit = report / "engine-rebuilds.json"
    save(audit, {"games": {}})
    campaign = {
        "id": "jev",
        "source_hashes": {},
        "model": "jev-1.14.0",
        "games": ["coin-run"],
        "seeds": [3000],
        "max_steps": 2,
        "mode": "exhibition",
        "version": old["version"],
        "timeout_s": 120,
        "prompt_version": PROMPT_VERSION,
        "warmup": "synthetic-gray-3/1",
        "base_campaign": "results/base/campaign.json",
        "base_snapshot_sha256": hashlib.sha256(previous).hexdigest(),
        "engine_rebuild_audit": "results/jev/engine-rebuilds.json",
        "engine_rebuild_sha256": hashlib.sha256(audit.read_bytes()).hexdigest(),
        "run_root": "runs/jev",
        "hardware_details": "Native image API.",
        "suite_file": "jev.json",
        "comparison_note": "Different transport conditions.",
    }
    save(report / "campaign.json", campaign)

    class FailedJev:
        model = "jev-1.14.0"
        metadata = {
            "requested_model": model,
            "resolved_models": [model],
            "prompt_version": PROMPT_VERSION,
            "transport": TRANSPORT,
            "action_schema": ACTION_SCHEMA,
            "observation": "png-only",
            "warmup": "synthetic-gray-3/1",
            "retries": 0,
            "tool_events": 0,
            "images_header": True,
            "image_preprocessing": IMAGE_PREPROCESSING,
        }

        def act(self, obs, timeout):
            raise ProtocolError("Failed model decision")

    new_path = tmp_path / "runs/jev/typesafe-jev-1.14.0/coin-run-3000"
    run_episode(
        FailedJev(), "typesafe-jev-1.14.0", "coin-run", 3000, new_path, 2, "exhibition", 120
    )
    save(
        new_path.parent / "status.json",
        {
            "agent": "typesafe-jev-1.14.0",
            "model": "jev-1.14.0",
            "provider": "typesafe",
            "status": "complete",
            "completed": 1,
        },
    )
    exporter.export(report)
    updated = json.loads(site.read_text())
    assert next(r for r in updated["exhibition"] if r["agent"] == "previous") == old_board[0]
    new = next(r for r in updated["exhibition"] if r["agent"] == "typesafe-jev-1.14.0")
    assert new["score"] == 0 and new["errors"] == 1 and new["aborted_episodes"] == 1
    assert updated["official"] == []
    assert (report / "previous-snapshot.json").read_bytes() == previous
