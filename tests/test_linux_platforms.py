"""Check platform selection without requiring a Docker daemon or a game runtime."""

import json
from pathlib import Path

import pytest

from generalgamebench.container_runtime import build_arguments, runtime_manifest
from generalgamebench.suites import EXTENDED_GAMES
from generalgamebench.unity_engine import asset_digest, unity_manifest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "machine,architecture", [("x86_64", "amd64"), ("aarch64", "arm64"), ("arm64", "arm64")]
)
def test_native_container_selection(monkeypatch, machine, architecture):
    monkeypatch.delenv("GGBENCH_CONTAINER_PLATFORM", raising=False)
    monkeypatch.setattr("generalgamebench.container_runtime.platform.machine", lambda: machine)
    for folder in sorted((ROOT / "environments").glob("docker-*")):
        original = json.loads((folder / "runtime.json").read_text())
        selected = runtime_manifest(folder)
        assert selected["platform"] == "linux/" + architecture
        assert selected["image"].endswith("-" + architecture)
        assert selected["engine_revision"] == original["engine_revision"]
        if architecture == "arm64":
            assert selected["image"] == original["image"]


def test_invalid_platform_and_build_count_fail(monkeypatch):
    with pytest.raises(ValueError, match="Unsupported engine platform"):
        runtime_manifest(ROOT / "environments/docker-football", "linux/riscv64")
    monkeypatch.setenv("GGBENCH_BUILD_JOBS", "0")
    with pytest.raises(ValueError, match="positive"):
        build_arguments()


def test_unity_uses_the_correct_pinned_binary():
    mac = unity_manifest("Darwin", "arm64")
    linux = unity_manifest("Linux", "x86_64")
    assert "/darwin/" in mac["url"]
    assert "/linux/" in linux["url"]
    assert linux["executable"] == "Startup.x86_64"
    assert mac["app_tree_sha256"] != linux["app_tree_sha256"]
    with pytest.raises(RuntimeError, match="Linux x86_64"):
        unity_manifest("Linux", "aarch64")


def test_unity_generated_timers_do_not_change_input_hash(tmp_path):
    (tmp_path / "Startup.x86_64").write_bytes(b"pinned executable")
    original = asset_digest(tmp_path)
    timers = tmp_path / "Startup_Data/ML-Agents/Timers"
    timers.mkdir(parents=True)
    (timers / "test.json").write_text("generated timing")
    assert asset_digest(tmp_path) == original
    (tmp_path / "Startup.x86_64").write_bytes(b"modified executable")
    assert asset_digest(tmp_path) != original


def test_linux_validation_covers_full_suite_once():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "validate_linux", ROOT / "scripts/validate_linux.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    runtimes = ["python", *(p.name for p in (ROOT / "environments").glob("docker-*"))]
    games = [game for runtime in runtimes for game in module.runtime_games(runtime)]
    assert len(games) == len(set(games)) == 43
    assert set(games) == set(EXTENDED_GAMES)
