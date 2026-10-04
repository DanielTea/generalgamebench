"""Build the pinned Football engine locally; no game binary is committed."""

import json
import shutil
import subprocess
from pathlib import Path


def main():
    folder = Path(__file__).resolve().parent
    manifest = json.loads((folder / "runtime.json").read_text())
    root = folder.parents[1]
    source = root / ".game-cache/football-build-source"
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
                manifest["repository"],
                str(source),
            ],
            check=True,
        )
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True)
    dirty = subprocess.check_output(
        ["git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"], text=True
    )
    if revision.strip() != manifest["engine_revision"] or dirty.strip():
        raise ValueError("Build source differs from the pinned clean revision")
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
    print("Football image built. Run the admission tests before comparing results.")


if __name__ == "__main__":
    main()
