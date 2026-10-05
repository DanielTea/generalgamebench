"""Build the pinned, explicitly patched Luanti/Craftium source and game snapshot."""

import hashlib
import shutil
import subprocess
from pathlib import Path

from generalgamebench.container_runtime import build_arguments, runtime_manifest


def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args])


def main():
    folder = Path(__file__).resolve().parent
    root = folder.parents[1]
    manifest = runtime_manifest(folder)
    patch = folder / "lockstep.patch"
    if hashlib.sha256(patch.read_bytes()).hexdigest() != manifest["patch_sha256"]:
        raise ValueError("Luanti patch differs from the pinned manifest")
    source = root / ".game-cache/craftium-build-source"
    if not source.exists():
        source.mkdir(parents=True)
        git(source, "init")
        git(source, "remote", "add", "origin", manifest["repository"])
        git(source, "fetch", "--depth", "1", "origin", manifest["engine_revision"])
        git(source, "checkout", "--detach", "FETCH_HEAD")
        git(source, "submodule", "update", "--init", "--depth", "1", *manifest["submodules"])
    if git(source, "rev-parse", "HEAD").decode().strip() != manifest["engine_revision"]:
        raise ValueError("Luanti source revision differs")
    for name, revision in manifest["submodules"].items():
        submodule = source / name
        if git(submodule, "rev-parse", "HEAD").decode().strip() != revision:
            raise ValueError(f"Luanti submodule revision differs: {name}")
        if git(submodule, "status", "--porcelain", "--untracked-files=no").strip():
            raise ValueError(f"Luanti submodule has modified source: {name}")
    dirty = git(source, "diff", "HEAD")
    if not dirty:
        git(source, "apply", str(patch))
        dirty = git(source, "diff", "HEAD")
    if dirty != patch.read_bytes():
        raise ValueError("Luanti source differs from the pinned patch")
    shutil.copyfile(folder / "Dockerfile", source / "Dockerfile.ggbench")
    shutil.copyfile(folder / "dockerignore", source / "Dockerfile.ggbench.dockerignore")
    subprocess.run(
        [
            "docker",
            "build",
            *build_arguments(),
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
    print("Luanti image built. Run the real-engine admission tests before comparing results.")


if __name__ == "__main__":
    main()
