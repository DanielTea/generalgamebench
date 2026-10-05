import json
import sys
import zipfile

import pytest

from generalgamebench.evidence import canonical
from generalgamebench.submission import (
    benchmark,
    prepare_uploads,
    verify_submission,
    verify_uploads,
)
from generalgamebench.suites import SUITES, Suite


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    monkeypatch.setitem(
        SUITES, "test-v1", Suite("test-v1", "Test suite", ("coin-run", "dodge-lanes"), (21, 22), 4)
    )
    output = tmp_path / "run"
    benchmark("test-v1", output, agent="idle", progress=lambda _: None)
    return output


def test_complete_campaign_and_archive_replay(campaign):
    result = verify_submission(campaign / "submission.zip")
    assert result["episodes"] == 4 and result["replayed"]
    assert result["authentication"] == "local-unattested"
    assert result["ranking"][0]["official_rank"] is None
    assert (campaign / "SUBMIT.txt").is_file()
    # Idempotent resume retains the exact original archive and timings.
    original = (campaign / "submission.zip").read_bytes()
    benchmark("test-v1", campaign, agent="idle", resume=True, progress=lambda _: None)
    assert (campaign / "submission.zip").read_bytes() == original


def test_resume_rejects_changed_policy(campaign):
    with pytest.raises(ValueError, match="original configuration"):
        benchmark("test-v1", campaign, agent="react", resume=True)


def test_missing_episode_and_forged_summary_rejected(campaign):
    root = campaign / "submission"
    path = root / "submission.json"
    manifest = json.loads(path.read_text())
    manifest["ranking"][0]["score"] = 99.123
    path.write_bytes(canonical(manifest))
    with pytest.raises(ValueError, match="ranking"):
        verify_submission(root)
    (root / "episodes/coin-run-21").rename(root / "episodes/missing")
    with pytest.raises(ValueError, match="episode set"):
        verify_submission(root)


def test_frame_and_result_edits_fail(campaign):
    root = campaign / "submission"
    result = root / "episodes/coin-run-21/result.json"
    original = result.read_bytes()
    value = json.loads(original)
    value["score"] = 0.555
    result.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Result file"):
        verify_submission(root)
    result.write_bytes(original)
    (root / "episodes/coin-run-21/frames/0000.png").write_bytes(b"forged")
    with pytest.raises(ValueError, match="digest"):
        verify_submission(root)


def test_unknown_suite_and_false_trust_rejected(campaign):
    root = campaign / "submission"
    path = root / "submission.json"
    original = json.loads(path.read_text())
    forged = {**original, "trust": "official"}
    path.write_text(json.dumps(forged))
    with pytest.raises(ValueError, match="trust"):
        verify_submission(root)
    original["suite"]["seeds"].append(999)
    path.write_text(json.dumps(original))
    with pytest.raises(ValueError, match="Suite definition"):
        verify_submission(root)


@pytest.mark.parametrize(
    "name", ["../outside", "/absolute", "episodes/../outside", "episodes\\evil", "agent.py"]
)
def test_archive_paths_and_code_are_rejected(tmp_path, name):
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(name, "bad")
    with pytest.raises(ValueError, match="archive member"):
        verify_submission(path)


def test_archive_links_and_duplicates_rejected(tmp_path):
    path = tmp_path / "link.zip"
    with zipfile.ZipFile(path, "w") as archive:
        info = zipfile.ZipInfo("submission.json")
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        archive.writestr(info, "/etc/passwd")
    with pytest.raises(ValueError, match="archive member"):
        verify_submission(path)
    path = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("submission.json", "{}")
        with pytest.warns(UserWarning):
            archive.writestr("submission.json", "{}")
    with pytest.raises(ValueError, match="archive member"):
        verify_submission(path)


def test_limits_and_extra_private_files_rejected(campaign, monkeypatch):
    monkeypatch.setattr("generalgamebench.submission.MAX_TOTAL", 5)
    with pytest.raises(ValueError, match="8 GiB"):
        verify_submission(campaign / "submission.zip")
    root = campaign / "submission"
    (root / ".env").write_text("not-for-upload")
    with pytest.raises(ValueError, match="Unexpected file"):
        verify_submission(root)


def test_verification_never_launches_agent(campaign, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Submitted agents must never execute during verification")

    monkeypatch.setattr("generalgamebench.submission.ProcessAgent", forbidden)
    assert verify_submission(campaign / "submission.zip")["valid"]


def test_custom_agent_requires_reproducibility_details(tmp_path):
    with pytest.raises(ValueError, match="revision"):
        benchmark(
            "starter-v1", tmp_path / "run", agent_command=f"{sys.executable} agent.py", name="mine"
        )


def test_published_suite_scope():
    assert len(SUITES["starter-v1"].games) == 2
    assert len(SUITES["portable-v1"].games) == 10
    assert len(SUITES["extended-v1"].games) == 43
    assert all(len(suite.games) == len(set(suite.games)) for suite in SUITES.values())


def test_upload_parts_reassemble_and_reject_missing_duplicate_corruption(
    campaign, tmp_path, monkeypatch
):
    monkeypatch.setattr("generalgamebench.submission.UPLOAD_CHUNK", 4096)
    parts = prepare_uploads(campaign / "submission.zip", tmp_path / "parts")
    assert len(parts) > 1
    assert verify_uploads(list(reversed(parts)))["valid"]
    with pytest.raises(ValueError, match="Missing upload"):
        verify_uploads(parts[:-1])
    with pytest.raises(ValueError, match="Duplicate upload"):
        verify_uploads(parts + parts[:1])
    with zipfile.ZipFile(parts[0]) as archive:
        meta = archive.read("part.json")
        payload = bytearray(archive.read("payload.bin"))
    payload[0] ^= 1
    with zipfile.ZipFile(parts[0], "w") as archive:
        archive.writestr("part.json", meta)
        archive.writestr("payload.bin", payload)
    with pytest.raises(ValueError, match="checksum"):
        verify_uploads(parts)


def test_resume_repairs_missing_upload_part_without_rerunning(campaign, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Completed campaigns must not rerun their agent")

    monkeypatch.setattr("generalgamebench.submission.ProcessAgent", forbidden)
    part = next((campaign / "uploads").glob("*.zip"))
    part.unlink()
    benchmark("test-v1", campaign, agent="idle", resume=True)
    assert verify_uploads([campaign / "uploads"])["valid"]
