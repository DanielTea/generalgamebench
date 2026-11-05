"""Run a declared Jev image campaign serially. Keep every scored failure."""

import argparse
import json
import re
from pathlib import Path

from export_refresh import verify_source
from run_campaign import warmup_agent

from generalgamebench.evidence import read_ledger, verify_episode
from generalgamebench.jev import JevAgent
from generalgamebench.runner import run_episode

ROOT = Path(__file__).resolve().parents[1]


def run(report):
    campaign = json.loads((report / "campaign.json").read_text())
    verify_source(campaign)
    if not re.fullmatch(r"jev-\d+\.\d+\.\d+", campaign["model"]):
        raise ValueError("Pin the resolved Jev version before recording")
    agent_id = "typesafe-" + campaign["model"]
    folder = ROOT / campaign["run_root"] / agent_id
    folder.mkdir(parents=True, exist_ok=True)
    status = {
        "agent": agent_id,
        "model": campaign["model"],
        "provider": "typesafe",
        "status": "running",
        "completed": 0,
    }
    status_path = folder / "status.json"
    status_path.write_text(json.dumps(status, indent=2) + "\n")
    agent = JevAgent(campaign["model"])
    try:
        warmup_agent(agent, campaign["warmup"])
        agent.metadata["warmup"] = campaign["warmup"]
        for game in campaign["games"]:
            for seed in campaign["seeds"]:
                output = folder / f"{game}-{seed}"
                if output.exists():
                    # A completed result is immutable. A partial result needs inspection.
                    previous = read_ledger(output / "events.jsonl")[-1]
                    if (
                        (output / "result.json").exists()
                        and json.loads((output / "result.json").read_text()) == previous
                        and (
                            previous["agent"],
                            previous["game"],
                            previous["seed"],
                            previous["max_steps"],
                            previous["response_timeout_seconds"],
                            previous["model"],
                        )
                        == (
                            agent_id,
                            game,
                            seed,
                            campaign["max_steps"],
                            campaign["timeout_s"],
                            campaign["model"],
                        )
                    ):
                        verify_episode(output, replay=False)
                        status["completed"] += 1
                        continue
                    raise ValueError("Preserve and inspect the existing incomplete episode")
                result = run_episode(
                    agent,
                    agent_id,
                    game,
                    seed,
                    output,
                    campaign["max_steps"],
                    campaign["mode"],
                    campaign["timeout_s"],
                )
                verify_episode(output, replay=False)
                status["completed"] += 1
                status_path.write_text(json.dumps(status, indent=2) + "\n")
                print(
                    json.dumps(
                        {
                            "game": game,
                            "score": result["score"],
                            "steps": result["steps"],
                            "errors": result["errors"],
                        }
                    ),
                    flush=True,
                )
                if result["aborted"]:
                    agent.close()
        verify_source(campaign)
        status["status"] = "complete"
    except Exception as exc:
        status["status"] = "blocked"
        status["error_type"] = type(exc).__name__
        raise
    finally:
        agent.close()
        status_path.write_text(json.dumps(status, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    run(parser.parse_args().report.resolve())
