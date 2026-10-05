"""Resumable real exhibition runs, one complete fixed suite per model.

Provider access failures are recorded separately, never converted into game wins.
Local models are evaluated serially to avoid overlapping GPU memory allocations.
"""

import argparse
import base64
import concurrent.futures
import io
import json
import os
import re
import secrets
from pathlib import Path

from generalgamebench import __version__
from generalgamebench.evidence import verify_episode
from generalgamebench.model_prompt import PROMPT_VERSION
from generalgamebench.models import CLIModelAgent
from generalgamebench.protocol import ProcessAgent
from generalgamebench.runner import run_episode

ROOT = Path(__file__).resolve().parents[1]
WARMUP_PROFILE = "synthetic-gray-3/1"


def warmup_agent(agent, profile):
    if profile != WARMUP_PROFILE:
        raise ValueError("Unknown model startup profile")
    from PIL import Image

    for size in ((160, 120), (320, 240), (960, 640)):
        image = io.BytesIO()
        Image.new("RGB", size, "gray").save(image, format="PNG")
        agent.act(
            {
                "protocol": "screenquest/1",
                "nonce": secrets.token_hex(16),
                "image_png": base64.b64encode(image.getvalue()).decode(),
                "actions": ["wait", "left", "right"],
                "instructions": "This is a startup check. Choose wait.",
            },
            120,
        )


def model_id(entry):
    return re.sub(r"[^a-zA-Z0-9_-]", "-", entry["provider"] + "-" + entry["model"])


def make_agent(entry):
    if entry["provider"] != "mlx":
        agent = CLIModelAgent(entry["provider"], entry["model"])
    else:
        python = os.environ.get("GGBENCH_MLX_PYTHON", str(ROOT / ".game-envs/vlm/bin/python"))
        agent = ProcessAgent(
            [python, str(ROOT / "src/generalgamebench/mlx_agent.py"), entry["local_path"]],
            startup_timeout=240,
        )
        agent.model = entry["model"]
        agent.metadata = {
            "transport": "persistent-mlx-jsonl",
            "requested_model": entry["model"],
            "revision": entry["revision"],
            "observation": "png-only",
            "temperature": 0.0,
            "thinking": False,
            "tool_events": 0,
            "prompt_version": PROMPT_VERSION,
        }
        if entry.get("warmup"):
            agent.metadata["warmup"] = entry["warmup"]
            try:
                warmup_agent(agent, entry["warmup"])
            except BaseException:
                agent.close()
                raise
    return agent


def evaluate(entry, args):
    name, agent, completed = model_id(entry), None, 0
    folder = args.output / name
    folder.mkdir(parents=True, exist_ok=True)
    status = {
        "agent": name,
        "provider": entry["provider"],
        "model": entry["model"],
        "revision": entry.get("revision"),
        "status": "running",
        "completed": 0,
    }
    status_file = folder / "status.json"
    try:
        for game in args.games:
            for seed in range(args.start_seed, args.start_seed + args.seeds):
                output = folder / f"{game}-{seed}"
                if (output / "result.json").exists():
                    previous = json.loads((output / "result.json").read_text())
                    metadata = previous["provider_metadata"]
                    if (
                        previous["agent"] != name
                        or previous["game"] != game
                        or previous["seed"] != seed
                        or previous["max_steps"] != args.steps
                        or previous["mode"] != "exhibition"
                        or previous["version"] != __version__
                        or previous.get("response_timeout_seconds") != args.timeout
                        or metadata.get("requested_model") != entry["model"]
                        or metadata.get("revision") != entry.get("revision")
                        or metadata.get("prompt_version") != PROMPT_VERSION
                        or metadata.get("warmup") != entry.get("warmup")
                    ):
                        raise ValueError(
                            "Existing episode configuration differs; use a new campaign directory"
                        )
                    verify_episode(output)
                    completed += 1
                    continue
                if output.exists():
                    raise ValueError(
                        "Incomplete episode directory; preserve and inspect before retry"
                    )
                if agent is None:
                    agent = make_agent(entry)
                result = run_episode(
                    agent, name, game, seed, output, args.steps, "exhibition", args.timeout
                )
                verify_episode(output)
                completed += 1
                status["completed"] = completed
                status_file.write_text(json.dumps(status, indent=2) + "\n")
                print(
                    json.dumps(
                        {
                            "agent": name,
                            "game": game,
                            "seed": seed,
                            "score": result["score"],
                            "steps": result["steps"],
                            "errors": result["errors"],
                        }
                    ),
                    flush=True,
                )
                if result["aborted"]:
                    agent.close()
                    agent = None
                    # A failed first call establishes no usable provider access.
                    # Keep that evidence but do not repeat a known outage 45 times.
                    if completed == 1 and result["errors"] == ["ProviderUnavailable"]:
                        status["status"] = "provider-unavailable"
                        return status
        status["status"] = "complete"
        status["completed"] = completed
    except Exception as exc:
        status["status"] = "blocked"
        status["error_type"] = type(exc).__name__
        print(
            json.dumps({"agent": name, "status": "blocked", "error_type": type(exc).__name__}),
            flush=True,
        )
    finally:
        if agent is not None:
            agent.close()
        status_file.write_text(json.dumps(status, indent=2) + "\n")
    return status


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inventory", type=Path, required=True)
    p.add_argument("--games", nargs="+", required=True)
    p.add_argument("--providers", nargs="+", default=["openai", "claude", "mlx"])
    p.add_argument("--seeds", type=int, default=2)
    p.add_argument("--start-seed", type=int, default=3000)
    p.add_argument("--steps", type=int, default=8)
    p.add_argument("--timeout", type=float, default=120)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if min(args.seeds, args.steps, args.workers, args.timeout) <= 0:
        p.error("Counts and timeout must be positive")
    entries = [
        m
        for m in json.loads(args.inventory.read_text())["models"]
        if m["provider"] in args.providers
    ]
    cloud = [m for m in entries if m["provider"] != "mlx"]
    local = [m for m in entries if m["provider"] == "mlx"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        statuses = list(pool.map(lambda e: evaluate(e, args), cloud))
    statuses.extend(evaluate(entry, args) for entry in local)
    (args.output / "campaign-status.json").write_text(json.dumps(statuses, indent=2) + "\n")


if __name__ == "__main__":
    main()
