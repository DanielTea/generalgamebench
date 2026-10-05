"""Compare fixed tasks while retaining each model's real inference conditions."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from generalgamebench import __version__
from generalgamebench.evidence import verify_episode
from generalgamebench.model_prompt import PROMPT_VERSION
from generalgamebench.ranking import summarize
from generalgamebench.runner import run_episode


@pytest.fixture
def exporter(monkeypatch):
    scripts = Path(__file__).parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location(
        "hosted_export", scripts / "export_hosted_rerun.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cohort(exporter):
    campaign = {
        "games": ["kart"],
        "seeds": [3000],
        "max_steps": 8,
        "mode": "exhibition",
        "version": "0.5.0",
        "timeout_s": 120,
        "prompt_version": "pixels-json-action/2",
    }
    local = {
        "agent": "local-model",
        "model": "local/model",
        "games": ["kart"],
        "seed_ids": [3000],
        "max_steps": 8,
        "mode": "exhibition",
        "hardware": "Darwin arm64",
        "version": "0.5.0",
        "task_metadata": {"kart": {"task_version": "3", "renderer": "v2"}},
        "response_timeout_seconds": 120,
        "latency_policy": exporter.policy(),
        "episodes": 1,
        "provider_metadata": {"prompt_version": "pixels-json-action/2"},
        "hardware_details": "Local model. Weights remain in memory.",
        "score": 12,
    }
    hosted = copy.deepcopy(local)
    hosted.update(
        agent="hosted-model",
        model="hosted/model",
        score=20,
        hardware_details="Hosted model. Each image starts a new command process.",
    )
    return campaign, local, hosted


def test_add_hosted_results_without_changing_verified_local_rows(exporter):
    campaign, local, hosted = cohort(exporter)
    original = copy.deepcopy(local)
    result = exporter.combine_board([local], [hosted], campaign)
    assert result == [hosted, local]
    assert local == original
    assert result[0]["hardware_details"] != result[1]["hardware_details"]


@pytest.mark.parametrize(
    "change",
    [
        {"task_metadata": {"kart": {"task_version": "2", "renderer": "v1"}}},
        {"seed_ids": [4000]},
        {"max_steps": 24},
        {"version": "0.4.0"},
        {"response_timeout_seconds": 60},
        {"latency_policy": {}},
        {"hardware": "Linux x86_64"},
        {"episodes": 0},
        {"hardware_details": None},
        {"provider_metadata": {"prompt_version": "different"}},
        {"model": None},
    ],
)
def test_reject_mixed_tasks_or_incomplete_test_conditions(exporter, change):
    campaign, local, hosted = cohort(exporter)
    with pytest.raises(ValueError):
        exporter.combine_board([local], [{**hosted, **change}], campaign)


def test_reject_duplicate_model_and_changed_declaration(exporter):
    campaign, local, hosted = cohort(exporter)
    with pytest.raises(ValueError, match="already exists"):
        exporter.combine_board([local], [{**hosted, "agent": local["agent"]}], campaign)
    campaign["seeds"] = [4000]
    with pytest.raises(ValueError, match="declaration"):
        exporter.combine_board([local], [hosted], campaign)


def test_refuse_to_overwrite_an_export(exporter, tmp_path):
    (tmp_path / "previous-snapshot.json").write_text("original")
    with pytest.raises(FileExistsError):
        exporter.export(tmp_path)
    assert (tmp_path / "previous-snapshot.json").read_text() == "original"


def publication_fixture(exporter, tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "ROOT", tmp_path)

    def save(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=1) + "\n")

    class Policy:
        def __init__(self, name, transport):
            self.model = name
            self.metadata = {
                "requested_model": name,
                "transport": transport,
                "prompt_version": PROMPT_VERSION,
                "tool_events": 0,
            }

        def act(self, obs, timeout):
            return {"nonce": obs["nonce"], "action": 0}

    games, seeds = ["coin-run"], [3000]
    local_path = tmp_path / "runs/local/local-test/coin-run-3000"
    local_row = run_episode(
        Policy("test/local", "persistent-mlx-jsonl"),
        "local-test",
        "coin-run",
        3000,
        local_path,
        2,
        "exhibition",
        120,
    )
    base_board = summarize([local_row], games, seeds)
    base_board[0]["hardware_details"] = "Local test conditions."
    base = tmp_path / "results/local"
    save(base / "campaign.json", {"games": games, "seeds": seeds, "source_hashes": {}})
    save(base / "episodes.json", [local_row])
    relative = str(local_path.relative_to(tmp_path))
    head = json.loads((local_path / "events.jsonl").read_text().splitlines()[-1])["hash"]
    save(base / "evidence-roots.json", {relative: head})
    save(base / "replay-validation.json", {relative: verify_episode(local_path)})
    snapshot = {
        "exhibition": base_board,
        "official": [],
        "local": [{"agent": "archive"}],
        "season": "local",
        "model_status": [{"agent": "local-test", "status": "complete", "completed": 1}],
        "campaigns": ["results/local/campaign.json"],
        "suite_files": ["local.json"],
        "track_metadata": {},
        "archives": [],
    }
    save(base / "snapshot.json", snapshot)
    site = tmp_path / "site/dist/data.json"
    save(site, snapshot)
    previous = site.read_bytes()
    report = tmp_path / "results/hosted"
    campaign = {
        "id": "hosted",
        "games": games,
        "seeds": seeds,
        "max_steps": 2,
        "mode": "exhibition",
        "version": __version__,
        "timeout_s": 120,
        "prompt_version": PROMPT_VERSION,
        "source_hashes": {},
        "base_campaign": "results/local/campaign.json",
        "run_root": "runs/hosted",
        "base_snapshot_sha256": hashlib.sha256(previous).hexdigest(),
        "hardware_details": "Hosted test conditions.",
        "comparison_note": "Different inference paths.",
        "suite_file": "hosted.json",
    }
    save(report / "campaign.json", campaign)
    entry = {"provider": "openai", "model": "test/hosted"}
    save(report / "model-inventory.json", {"models": [entry]})
    agent = exporter.model_id(entry)
    path = tmp_path / "runs/hosted" / agent / "coin-run-3000"
    run_episode(
        Policy(entry["model"], "authenticated-cli-per-frame"),
        agent,
        "coin-run",
        3000,
        path,
        2,
        "exhibition",
        120,
    )
    save(
        path.parent / "status.json",
        {
            "agent": agent,
            "provider": "openai",
            "model": entry["model"],
            "status": "complete",
            "completed": 1,
        },
    )
    return report, previous, path


def test_export_preserves_local_rows_and_exact_previous_bytes(exporter, tmp_path, monkeypatch):
    report, previous, _ = publication_fixture(exporter, tmp_path, monkeypatch)
    exporter.export(report, 1)
    result = json.loads((report / "snapshot.json").read_text())
    old = json.loads(previous)
    assert len(result["exhibition"]) == 2
    assert (
        next(r for r in result["exhibition"] if r["agent"] == "local-test") == old["exhibition"][0]
    )
    assert result["local"] == old["local"] and result["official"] == old["official"]
    assert (report / "previous-snapshot.json").read_bytes() == previous
    assert (report / "snapshot.json").read_bytes() == (
        tmp_path / "site/dist/data.json"
    ).read_bytes()
    assert len(json.loads((report / "episodes.json").read_text())) == 2


@pytest.mark.parametrize("fault", ["changed_sidecar", "incomplete_status", "extra_episode"])
def test_export_rejects_inconsistent_evidence_before_publication(
    exporter, tmp_path, monkeypatch, fault
):
    report, previous, path = publication_fixture(exporter, tmp_path, monkeypatch)
    if fault == "changed_sidecar":
        data = json.loads((path / "result.json").read_text())
        data["score"] = 1
        (path / "result.json").write_text(json.dumps(data))
    elif fault == "incomplete_status":
        status = path.parent / "status.json"
        data = json.loads(status.read_text())
        data["status"] = "blocked"
        status.write_text(json.dumps(data))
    else:
        (path.parent / "unexpected-3000").mkdir()
    with pytest.raises(ValueError):
        exporter.export(report, 1)
    assert not (report / "snapshot.json").exists()
    assert (tmp_path / "site/dist/data.json").read_bytes() == previous
