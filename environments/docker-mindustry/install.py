"""Build Mindustry and its missing Linux ARM64 display binding from pinned inputs."""

import hashlib
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from generalgamebench.container_runtime import build_arguments, runtime_manifest


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    folder = Path(__file__).resolve().parent
    root = folder.parents[1]
    manifest = runtime_manifest(folder)
    patch = folder / "clock.patch"
    if digest(patch) != manifest["patch_sha256"]:
        raise ValueError("Mindustry clock patch differs from the pinned manifest")
    cache = root / ".game-cache/mindustry-artifacts"
    cache.mkdir(parents=True, exist_ok=True)
    for name, artifact in manifest["artifacts"].items():
        target = cache / name
        if not target.exists():
            temporary = target.with_suffix(".download")
            urllib.request.urlretrieve(artifact["url"], temporary)
            if digest(temporary) != artifact["sha256"]:
                raise ValueError(f"Downloaded Mindustry input checksum differs: {name}")
            temporary.replace(target)
        if digest(target) != artifact["sha256"]:
            raise ValueError(f"Cached Mindustry input checksum differs: {name}")
    with tempfile.TemporaryDirectory(prefix="mindustry-build-", dir=root / ".game-cache") as tmp:
        build = Path(tmp)
        for name in manifest["artifacts"]:
            shutil.copyfile(cache / name, build / name)
        with tarfile.open(build / "arc.tar.gz") as archive:
            archive.extractall(build, filter="data")
        extracted = build / f"Arc-{manifest['arc_revision']}"
        extracted.rename(build / "arc")
        subprocess.run(
            ["patch", "--batch", "--fuzz=0", "-p1", "-i", str(patch)], cwd=build / "arc", check=True
        )
        for name in ("Generate.java", "BenchmarkLauncher.java", "Dockerfile"):
            shutil.copyfile(folder / name, build / name)
        shutil.copyfile(folder / "dockerignore", build / ".dockerignore")
        subprocess.run(
            [
                "docker",
                "build",
                *build_arguments(),
                "--platform",
                manifest["platform"],
                "-t",
                manifest["image"],
                ".",
            ],
            cwd=build,
            check=True,
        )
    print("Mindustry image built. Run the real-engine admission tests before comparing results.")


if __name__ == "__main__":
    main()
