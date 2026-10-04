"""Actual model gameplay; no synthetic scores. Uses existing CLI sign-ins."""

import argparse
import json
from pathlib import Path

from screenquest_arena.models import CLIModelAgent
from screenquest_arena.runner import run_episode

p = argparse.ArgumentParser()
p.add_argument("provider", choices=["astra", "claude"])
p.add_argument("--model", required=True)
p.add_argument("--games", nargs="+", default=["coin-run", "dodge-lanes", "doom-basic"])
p.add_argument("--seeds", type=int, default=2)
p.add_argument("--steps", type=int, default=8)
p.add_argument("--output", type=Path, default=Path("runs/exhibition"))
a = p.parse_args()
for game in a.games:
    for seed in range(2000, 2000 + a.seeds):
        agent = CLIModelAgent(a.provider, a.model)
        try:
            result = run_episode(
                agent,
                a.provider,
                game,
                seed,
                a.output / a.provider / f"{game}-{seed}",
                a.steps,
                "exhibition",
                90,
            )
            print(
                json.dumps(
                    {
                        k: result[k]
                        for k in ("agent", "game", "seed", "score", "steps", "errors", "model")
                    }
                ),
                flush=True,
            )
        finally:
            agent.close()
