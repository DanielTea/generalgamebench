"""Resolve the latest Jev model using unscored synthetic image requests."""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from run_campaign import WARMUP_PROFILE, warmup_agent

from generalgamebench.jev import JevAgent


def preflight():
    agent = JevAgent("jev-latest")
    try:
        inventory = agent.list_models()
        warmup_agent(agent, WARMUP_PROFILE)
        if not re.fullmatch(r"jev-\d+\.\d+\.\d+", agent.model):
            raise ValueError("The latest alias did not resolve to a pinned model version")
        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "requested_alias": "jev-latest",
            "resolved_model": agent.model,
            "models": inventory["models"],
            "image_input": True,
            "synthetic_profile": WARMUP_PROFILE,
            "scope": "Unscored gray images only. No benchmark game frames.",
        }
    finally:
        agent.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Preserve the existing preflight record. Use a new output path.")
    result = preflight()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
