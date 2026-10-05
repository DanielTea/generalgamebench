"""Record and replay every scenario assigned to one Linux runtime group."""

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

from generalgamebench.evidence import verify_episode
from generalgamebench.games import DOOM, NATIVE
from generalgamebench.protocol import ProcessAgent
from generalgamebench.registry import TASKS
from generalgamebench.runner import run_episode


def runtime_games(runtime):
    if runtime == "python":
        return [
            *NATIVE,
            *DOOM,
            *(name for name, task in TASKS.items() if not task.runtime.startswith("docker-")),
        ]
    games = [name for name, task in TASKS.items() if task.runtime == runtime]
    if not games:
        raise ValueError("Unknown or empty runtime group")
    return games


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        parser.error("These checks require native Linux x86_64.")
    args.output.mkdir(parents=True, exist_ok=False)
    games, results = runtime_games(args.runtime), {}
    for game in games:
        episode = args.output / game
        agent = ProcessAgent([sys.executable, "-m", "generalgamebench.baselines", "random"])
        try:
            row = run_episode(agent, "linux-admission-random", game, 71, episode, 24, "exhibition")
        finally:
            agent.close()
        if row["errors"] or row["aborted"]:
            raise ValueError(f"The referee failed for {game}.")
        results[game] = verify_episode(episode)
        print(f"Native frame and score replay passed: {game}", flush=True)
    report = {
        "runtime": args.runtime,
        "platform": "linux/amd64",
        "games": games,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "seed": 71,
        "max_steps": 24,
        "results": results,
    }
    (args.output / "validation.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
