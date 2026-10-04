"""Portable command line. Runs are local/provisional until independent verification exists."""

import argparse
import json
import shlex
import sys
from pathlib import Path

from .evidence import verify_episode
from .games import DOOM, NATIVE
from .protocol import ProcessAgent
from .ranking import summarize
from .runner import run_episode


def main():
    parser = argparse.ArgumentParser(prog="generalgamebench")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("games")
    run = sub.add_parser("run")
    run.add_argument("--agent", choices=["idle", "random", "react", "tracker"], default="react")
    run.add_argument(
        "--agent-command", help="Local JSONL executable, shell syntax for arguments only"
    )
    run.add_argument("--name", help="Name for a custom agent")
    run.add_argument("--games", nargs="+", default=list(NATIVE))
    run.add_argument("--seeds", type=int, default=10)
    run.add_argument("--start-seed", type=int, default=1000)
    run.add_argument("--steps", type=int, default=80)
    run.add_argument("--mode", choices=["realtime", "exhibition"], default="realtime")
    run.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("episode", type=Path)
    verify.add_argument("--no-replay", action="store_true")
    board = sub.add_parser("rank")
    board.add_argument("runs", type=Path)
    board.add_argument("--games", nargs="+", required=True)
    board.add_argument("--seeds", type=int, default=10)
    board.add_argument("--start-seed", type=int, default=1000)
    board.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "games":
        print(json.dumps({"bundled_original_2d": NATIVE, "optional_vizdoom_3d": DOOM}, indent=2))
    elif args.command == "verify":
        print(json.dumps(verify_episode(args.episode, replay=not args.no_replay), indent=2))
    elif args.command == "run":
        if args.seeds < 1 or args.steps < 1 or any(g not in NATIVE + DOOM for g in args.games):
            parser.error("Use positive seeds/steps and known game IDs")
        if args.agent_command and not args.name:
            parser.error("--name is required for a custom agent")
        command = (
            shlex.split(args.agent_command)
            if args.agent_command
            else [sys.executable, "-m", "generalgamebench.baselines", args.agent]
        )
        name = args.name or args.agent
        if not name or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for c in name
        ):
            parser.error("Agent name must contain only letters, digits, hyphens and underscores")
        for game in args.games:
            for seed in range(args.start_seed, args.start_seed + args.seeds):
                agent = ProcessAgent(command)
                try:
                    result = run_episode(
                        agent,
                        name,
                        game,
                        seed,
                        args.output / name / f"{game}-{seed}",
                        args.steps,
                        args.mode,
                    )
                    print(
                        json.dumps(
                            {
                                k: result[k]
                                for k in (
                                    "agent",
                                    "game",
                                    "seed",
                                    "score",
                                    "latency_eligible",
                                    "errors",
                                )
                            }
                        ),
                        flush=True,
                    )
                finally:
                    agent.close()
    elif args.command == "rank":
        results = []
        for path in sorted(args.runs.rglob("result.json")):
            # Verify evidence before treating its final record as the result.
            verify_episode(path.parent, replay=True)
            from .evidence import read_ledger

            results.append(read_ledger(path.parent / "events.jsonl")[-1])
        rankings = summarize(
            results, args.games, list(range(args.start_seed, args.start_seed + args.seeds))
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"rankings": rankings}, indent=2))
        print(args.output)


if __name__ == "__main__":
    main()
