"""Install the full suite on Linux x86_64. Keep each Python runtime separate."""

import argparse
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_RUNTIMES = {
    "procgen": "3.10.12",
    "research": "3.12",
    "roguelike": "3.12",
    "unity": "3.10.12",
}
CONTAINER_RUNTIMES = sorted(
    path.parent.name for path in (ROOT / "environments").glob("docker-*/runtime.json")
)
SYSTEM_PACKAGES = [
    "build-essential",
    "cmake",
    "ninja-build",
    "pkg-config",
    "git",
    "patch",
    "curl",
    "bison",
    "flex",
    "libncurses-dev",
    "libjpeg-dev",
    "libpng-dev",
    "zlib1g-dev",
    "libgl1",
    "libglu1-mesa",
    "libgl1-mesa-dri",
    "libegl1",
    "libglib2.0-0",
    "libsdl2-2.0-0",
    "libsndfile1",
    "libopenal1",
    "libgomp1",
    "libx11-6",
    "libxcursor1",
    "libxrandr2",
    "libxi6",
    "libasound2t64",
    "xvfb",
    "xauth",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime", nargs="+", choices=["python", *PYTHON_RUNTIMES, *CONTAINER_RUNTIMES]
    )
    parser.add_argument(
        "--system-packages",
        action="store_true",
        help="Print the Ubuntu 24.04 package list and exit.",
    )
    args = parser.parse_args()
    if args.system_packages:
        print(" ".join(SYSTEM_PACKAGES))
        return
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "AMD64"}:
        parser.error("The full Linux suite requires x86_64. Use the Mac instructions on macOS.")
    uv = shutil.which("uv")
    if not uv:
        parser.error("Install uv first. See environments/linux/README.md.")
    selected = args.runtime or [*PYTHON_RUNTIMES, *CONTAINER_RUNTIMES]
    if "python" in selected:
        selected = list(dict.fromkeys([*PYTHON_RUNTIMES, *(x for x in selected if x != "python")]))
    for name in selected:
        if name in PYTHON_RUNTIMES:
            folder = ROOT / ".game-envs" / name
            if not (folder / "bin/python").exists():
                subprocess.run(
                    [uv, "venv", "--python", PYTHON_RUNTIMES[name], str(folder)], check=True
                )
            subprocess.run(
                [
                    uv,
                    "pip",
                    "sync",
                    "--python",
                    str(folder / "bin/python"),
                    str(ROOT / "environments" / name / "requirements.lock"),
                ],
                check=True,
            )
            if name == "unity":
                subprocess.run(
                    [uv, "run", "--no-sync", "python", "environments/unity/install.py"],
                    cwd=ROOT,
                    check=True,
                )
        else:
            subprocess.run(
                [uv, "run", "--no-sync", "python", f"environments/{name}/install.py"],
                cwd=ROOT,
                check=True,
            )
    print("Runtime installation is complete. Run the full suite check before a benchmark.")


if __name__ == "__main__":
    main()
