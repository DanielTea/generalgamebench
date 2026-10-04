"""Build the pinned, explicitly patched OpenTTD source and game snapshot."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args])


def main():
    folder = Path(__file__).resolve().parent
    root = folder.parents[1]
    manifest = json.loads((folder / "runtime.json").read_text())
    patch = folder / "lockstep.patch"
    if hashlib.sha256(patch.read_bytes()).hexdigest() != manifest["patch_sha256"]:
        raise ValueError("OpenTTD patch differs from the pinned manifest")
    source = root / ".game-cache/openttd-build-source"
    if not source.exists():
        source.mkdir(parents=True)
        git(source, "init")
        git(source, "remote", "add", "origin", manifest["repository"])
        git(source, "fetch", "--depth", "1", "origin", manifest["engine_revision"])
        git(source, "checkout", "--detach", "FETCH_HEAD")
        if manifest["submodules"]:
            git(source, "submodule", "update", "--init", "--depth", "1", *manifest["submodules"])
    if git(source, "rev-parse", "HEAD").decode().strip() != manifest["engine_revision"]:
        raise ValueError("OpenTTD source revision differs")
    for name, revision in manifest["submodules"].items():
        submodule = source / name
        if git(submodule, "rev-parse", "HEAD").decode().strip() != revision:
            raise ValueError(f"OpenTTD submodule revision differs: {name}")
        if git(submodule, "status", "--porcelain", "--untracked-files=no").strip():
            raise ValueError(f"OpenTTD submodule has modified source: {name}")
    dirty = git(source, "diff", "HEAD")
    if not dirty:
        git(source, "apply", str(patch))
        dirty = git(source, "diff", "HEAD")
    if dirty != patch.read_bytes():
        raise ValueError("OpenTTD source differs from the pinned patch")
    (source / ".ottdrev").write_text(
        "15.3+ggbench1\t20260404\t2\t14ec60f248547d4d062a1160f0fc26d742319888\t0\t0\n"
    )
    for name in ("assets-hashes.json", "verify-assets.py"):
        shutil.copyfile(folder / name, source / name)
    shutil.copyfile(folder / "Dockerfile", source / "Dockerfile.ggbench")
    shutil.copyfile(folder / "dockerignore", source / "Dockerfile.ggbench.dockerignore")
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
    print("OpenTTD image built. Run the real-engine admission tests before comparing results.")


if __name__ == "__main__":
    main()
