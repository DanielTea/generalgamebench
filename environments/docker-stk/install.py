"""Build the GPL engine variant and install verified upstream assets separately."""

import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath

from generalgamebench.container_runtime import asset_digest


def install_assets(root, manifest):
    destination = root / manifest["assets_directory"]
    if destination.exists():
        if asset_digest(destination / "data") != manifest["assets_tree_sha256"]:
            raise ValueError("Existing STK assets differ; inspect them before reinstalling")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        temporary = Path(temporary)
        archive = temporary / "upstream.tar.gz"
        digest = hashlib.sha256()
        with urllib.request.urlopen(manifest["assets_url"], timeout=120) as response:
            with archive.open("wb") as file:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    file.write(chunk)
                    digest.update(chunk)
        if digest.hexdigest() != manifest["assets_archive_sha256"]:
            raise ValueError("Upstream STK archive checksum mismatch")
        extracted = temporary / "extracted"
        data = extracted / "data"
        data.mkdir(parents=True)
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar:
                parts = PurePosixPath(member.name).parts
                if len(parts) < 3 or parts[1] != "data":
                    continue
                target = data.joinpath(*parts[2:])
                if not target.resolve().is_relative_to(data.resolve()):
                    raise ValueError("Unsafe upstream archive path")
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as source, target.open("wb") as file:
                        shutil.copyfileobj(source, file)
                else:
                    raise ValueError("Unexpected link or special file in upstream game assets")
        if asset_digest(data) != manifest["assets_tree_sha256"]:
            raise ValueError("Extracted STK asset checksum mismatch")
        extracted.rename(destination)


def main():
    folder = Path(__file__).resolve().parent
    root = folder.parents[1]
    manifest = json.loads((folder / "runtime.json").read_text())
    patch = folder / "simulation-clock.patch"
    if hashlib.sha256(patch.read_bytes()).hexdigest() != manifest["patch_sha256"]:
        raise ValueError("Engine patch differs from the task manifest")
    source = root / ".game-cache/stk-build-source"
    source.parent.mkdir(exist_ok=True)
    if not source.exists():
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                manifest["tag"],
                "--recurse-submodules",
                manifest["repository"],
                str(source),
            ],
            check=True,
        )
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True)
    if revision.strip() != manifest["engine_revision"]:
        raise ValueError("STK build source revision differs")
    submodule = source / "lib/pybind11"
    subrevision = subprocess.check_output(
        ["git", "-C", str(submodule), "rev-parse", "HEAD"], text=True
    ).strip()
    if subrevision != "1b4990838904501de7110d27e96c0a4152029156":
        raise ValueError("STK pybind11 submodule revision differs")
    dirty = subprocess.check_output(["git", "-C", str(source), "diff", "HEAD"])
    if not dirty:
        subprocess.run(["git", "-C", str(source), "apply", str(patch)], check=True)
        dirty = subprocess.check_output(["git", "-C", str(source), "diff", "HEAD"])
    if dirty != patch.read_bytes():
        raise ValueError("STK build source differs from the pinned patch")
    install_assets(root, manifest)
    shutil.copyfile(folder / "Dockerfile", source / "Dockerfile.ggbench")
    shutil.copyfile(folder / "dockerignore", source / ".dockerignore")
    subprocess.run(
        [
            "docker",
            "build",
            "--platform",
            manifest["platform"],
            "-f",
            "Dockerfile.ggbench",
            "-t",
            manifest["image"],
            ".",
        ],
        cwd=source,
        check=True,
    )
    print("STK engine and assets installed. Run the real-engine admission checks next.")


if __name__ == "__main__":
    main()
