"""Launch trusted game engines in pinned local images, never participant code.

The image contains the engine and its assets. Only the referee's worker source is
mounted; account credentials, Docker's socket and model caches are not mounted.
This is dependency isolation, not a claim of a hostile-agent evaluation service.
"""

import hashlib
import json
import shutil
import subprocess
import uuid
from pathlib import Path


def asset_digest(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Unexpected symlink in game assets")
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode() + b"\0")
            file_digest = hashlib.sha256()
            with path.open("rb") as file:
                for chunk in iter(lambda: file.read(1024 * 1024), b""):
                    file_digest.update(chunk)
            digest.update(file_digest.digest())
    return digest.hexdigest()


def container_command(runtime):
    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError("Docker is required for this engine; see environments/README.md")
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "environments" / runtime / "runtime.json").read_text())
    try:
        inspection = subprocess.run(
            [docker, "image", "inspect", manifest["image"]],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        info = json.loads(inspection.stdout)[0]
    except (subprocess.SubprocessError, ValueError, IndexError) as exc:
        raise RuntimeError(f"Build the {runtime} image; see environments/{runtime}") from exc
    labels = info["Config"].get("Labels") or {}
    if labels.get("org.generalgamebench.engine-revision") != manifest["engine_revision"]:
        raise ValueError("Game image does not match the pinned engine revision")
    if f"{info['Os']}/{info['Architecture']}" != manifest["platform"]:
        raise ValueError("Game image does not match the validated platform")
    if "variant" in manifest and labels.get("org.generalgamebench.variant") != manifest["variant"]:
        raise ValueError("Game image does not match the validated engine variant")
    name = "ggbench-" + uuid.uuid4().hex
    command = [
        docker,
        "run",
        "--rm",
        "--init",
        "-i",
        "--name",
        name,
        "--network",
        "none",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,size=1g" + (",exec" if manifest.get("temporary_engine_copy") else ""),
        "--workdir",
        "/tmp",
        "--env",
        "HOME=/tmp",
        "--env",
        "PYTHONHASHSEED=0",
        "--mount",
        f"type=bind,src={Path(__file__).parent},dst=/worker,readonly",
        info["Id"],
        "/worker/environment_worker.py",
    ]
    metadata = {
        "container_image": info["Id"],
        "container_architecture": info["Architecture"],
        "engine_revision": manifest["engine_revision"],
    }
    if "variant" in manifest:
        metadata["engine_variant"] = manifest["variant"]
    if "assets_directory" in manifest:
        assets = root / manifest["assets_directory"]
        if not assets.is_dir() or asset_digest(assets / "data") != manifest["assets_tree_sha256"]:
            raise ValueError(f"Install the pinned {runtime} assets; input checksum mismatch")
        command[-2:-2] = ["--mount", f"type=bind,src={assets},dst=/assets,readonly"]
        metadata["assets_sha256"] = manifest["assets_tree_sha256"]
    return command, metadata, [docker, "rm", "--force", name]
