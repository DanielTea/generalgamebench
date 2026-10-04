"""Build the pinned, explicitly patched Warzone 2100 source and game snapshot."""

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
        raise ValueError("Warzone 2100 patch differs from the pinned manifest")
    source = root / ".game-cache/warzone-build-source"
    if not source.exists():
        source.mkdir(parents=True)
        git(source, "init")
        git(source, "remote", "add", "origin", manifest["repository"])
        git(source, "fetch", "--depth", "1", "origin", manifest["engine_revision"])
        git(source, "checkout", "--detach", "FETCH_HEAD")
        if manifest["submodules"]:
            git(source, "submodule", "update", "--init", "--recursive", "--depth", "1")
    if git(source, "rev-parse", "HEAD").decode().strip() != manifest["engine_revision"]:
        raise ValueError("Warzone 2100 source revision differs")
    for name, revision in manifest["submodules"].items():
        submodule = source / name
        if git(submodule, "rev-parse", "HEAD").decode().strip() != revision:
            raise ValueError(f"Warzone 2100 submodule revision differs: {name}")
        if git(submodule, "status", "--porcelain", "--untracked-files=no").strip():
            raise ValueError(f"Warzone 2100 submodule has modified source: {name}")
    dirty = git(source, "diff", "HEAD")
    if not dirty:
        git(source, "apply", str(patch))
        dirty = git(source, "diff", "HEAD")
    if dirty != patch.read_bytes():
        raise ValueError("Warzone 2100 source differs from the pinned patch")
    import urllib.request

    version_cache = folder / "autorevision.cache"
    if hashlib.sha256(version_cache.read_bytes()).hexdigest() != manifest["version_cache_sha256"]:
        raise ValueError("Warzone source version cache differs")
    shutil.copyfile(version_cache, source / "build_tools/autorevision.cache")
    archive = root / ".game-cache/SDL3-3.2.26.tar.gz"
    if not archive.exists():
        urllib.request.urlretrieve(manifest["sdl_archive_url"], archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["sdl_archive_sha256"]:
        raise ValueError("SDL3 source checksum mismatch")
    shutil.copyfile(archive, source / "SDL3.tar.gz")
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
    print("Warzone 2100 image built. Run the real-engine admission tests before comparing results.")


if __name__ == "__main__":
    main()
