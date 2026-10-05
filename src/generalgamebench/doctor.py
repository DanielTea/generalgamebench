"""Read-only installation checks with actionable remedies, without calling models."""

import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path

from .games import DOOM
from .registry import TASKS
from .suites import SUITES


def diagnose(suite_id):
    suite = SUITES[suite_id]
    checks = []

    def add(name, ready, detail):
        checks.append({"name": name, "ready": bool(ready), "detail": detail})

    add("Python", sys.version_info >= (3, 11), platform.python_version())
    add(
        "Operating system",
        os.name == "posix",
        "Native Windows pipes are unsupported. Use the Docker image or WSL2."
        if os.name != "posix"
        else f"{platform.system()} {platform.machine()}",
    )
    if any(game in DOOM for game in suite.games):
        installed = importlib.util.find_spec("vizdoom") is not None
        add("ViZDoom", installed, "Installed" if installed else "Run uv sync --frozen --extra doom")
    root = Path(__file__).resolve().parents[2]
    home = Path(os.environ.get("GGBENCH_ENV_ROOT", root / ".game-envs"))
    runtimes = sorted({TASKS[game].runtime for game in suite.games if game in TASKS})
    for runtime in runtimes:
        if runtime.startswith("docker-"):
            from .container_runtime import container_command

            try:
                _, metadata, _ = container_command(runtime)
                add(runtime, True, metadata["container_image"])
            except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as exc:
                add(runtime, False, f"{exc}. Run uv run python environments/{runtime}/install.py")
        else:
            python = home / runtime / "bin/python"
            add(
                runtime,
                python.is_file(),
                "Installed; gameplay is checked during replay"
                if python.is_file()
                else f"Install the {runtime} runtime using environments/README.md",
            )
    return {
        "suite": suite_id,
        "games": len(suite.games),
        "episodes": len(suite.games) * len(suite.seeds),
        "ready": all(item["ready"] for item in checks),
        "checks": checks,
        "scope": "Installation checks only; benchmark runs verify native gameplay and replay.",
    }
