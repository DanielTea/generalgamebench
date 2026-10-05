"""Fail-closed engine selection and the host/container filesystem boundary."""

import json
from types import SimpleNamespace

import pytest

from generalgamebench import container_runtime


@pytest.fixture(params=["arm64", "amd64"])
def architecture(request, monkeypatch):
    monkeypatch.setenv("GGBENCH_CONTAINER_PLATFORM", "linux/" + request.param)
    return request.param


def image_info(architecture):
    return {
        "Id": "sha256:" + "a" * 64,
        "Os": "linux",
        "Architecture": architecture,
        "Config": {
            "Labels": {
                "org.generalgamebench.engine-revision": "ba9952130898bde2879b01ff2b49d3d48d26ce81"
            }
        },
    }


def install_inspection(monkeypatch, info):
    monkeypatch.setattr(container_runtime.shutil, "which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr(
        container_runtime.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps([info])),
    )


def test_engine_uses_immutable_image_and_only_worker_mount(monkeypatch, architecture):
    info = image_info(architecture)
    install_inspection(monkeypatch, info)
    command, metadata, cleanup = container_runtime.container_command("docker-football")
    assert info["Id"] in command
    assert f"ggbench-football:2.10.2-{architecture}" not in command
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert command[command.index("--tmpfs") + 1] == "/tmp:rw,size=1g"
    assert command.count("--mount") == 1
    mount = command[command.index("--mount") + 1]
    assert mount.endswith("/generalgamebench,dst=/worker,readonly")
    assert metadata["container_image"] == info["Id"]
    assert cleanup[-1] == command[command.index("--name") + 1]


def test_craftium_can_execute_its_temporary_engine_copy(monkeypatch, architecture):
    info = image_info(architecture)
    info["Config"]["Labels"] = {
        "org.generalgamebench.engine-revision": "8cffe4176e793f78d00b17fa7e46ccf333a7b5b0",
        "org.generalgamebench.variant": "serial-lockstep-v2",
    }
    install_inspection(monkeypatch, info)
    command, metadata, _ = container_runtime.container_command("docker-craftium")
    assert command[command.index("--tmpfs") + 1] == "/tmp:rw,size=1g,exec"
    assert "--read-only" in command
    assert command.count("--mount") == 1
    assert metadata["engine_variant"] == "serial-lockstep-v2"


@pytest.mark.parametrize("changed", ["revision", "architecture"])
def test_unverified_engine_is_rejected(monkeypatch, changed, architecture):
    info = image_info(architecture)
    if changed == "revision":
        info["Config"]["Labels"] = {}
    else:
        info["Architecture"] = "amd64" if architecture == "arm64" else "arm64"
    install_inspection(monkeypatch, info)
    with pytest.raises(ValueError, match="does not match"):
        container_runtime.container_command("docker-football")


def test_asset_digest_detects_changes_and_rejects_external_links(tmp_path):
    asset = tmp_path / "level.dat"
    asset.write_bytes(b"pinned level")
    expected = container_runtime.asset_digest(tmp_path)
    asset.write_bytes(b"modified level")
    assert container_runtime.asset_digest(tmp_path) != expected
    (tmp_path / "outside").symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        container_runtime.asset_digest(tmp_path)
