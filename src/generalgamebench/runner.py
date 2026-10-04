"""One referee owns clocks, random seeds, accepted actions, scores and evidence."""

import base64
import json
import platform
import secrets
import time
from pathlib import Path

from . import __version__
from .evidence import Ledger, digest
from .games import make_game
from .protocol import ProtocolError, validate_reply


def run_episode(
    agent,
    agent_id: str,
    game_id: str,
    seed: int,
    output: Path,
    max_steps: int = 80,
    mode: str = "realtime",
    timeout: float = 60,
) -> dict:
    if mode not in {"realtime", "exhibition"} or max_steps < 1 or timeout <= 0:
        raise ValueError("Invalid run configuration")
    output.mkdir(parents=True, exist_ok=False)
    (output / "frames").mkdir()
    from PIL import Image

    Image.init()  # Fixed codec warmup before all scored episodes.
    game, ledger = make_game(game_id, seed, max_steps), Ledger(output / "events.jsonl")
    # Seeds are in the referee's private manifest, never in agent observations.
    manifest = {
        "type": "manifest",
        "version": __version__,
        "agent": agent_id,
        "game": game_id,
        "seed": seed,
        "max_steps": max_steps,
        "mode": mode,
        "actions": game.actions,
        "hardware": f"{platform.system()} {platform.machine()}",
        "timing": "capture-start to validated action receipt; includes PNG and IPC",
        "simulation": "lockstep; late actions replaced with wait in realtime mode",
        "trust": "local-unattested",
        "created_at": time.time(),
    }
    ledger.append(manifest)
    latencies, errors, aborted = [], [], False
    try:
        while not game.done:
            started = time.perf_counter_ns()
            frame = game.frame()
            nonce = secrets.token_hex(16)
            obs = {
                "protocol": "screenquest/1",
                "nonce": nonce,
                "image_png": base64.b64encode(frame).decode(),
                "actions": game.actions,
                "instructions": game.instructions,
            }
            reply, error, action = None, None, 0
            try:
                budget = (
                    max(0.000001, 0.1 - (time.perf_counter_ns() - started) / 1e9)
                    if mode == "realtime"
                    else timeout
                )
                reply = agent.act(obs, budget)
                action = validate_reply(reply, obs)
            except (TimeoutError, ProtocolError, BrokenPipeError, OSError, ValueError) as exc:
                error = type(exc).__name__
                errors.append(error)
                aborted = True
            accepted = time.perf_counter_ns()
            latency = (accepted - started) / 1e6
            applied = 0 if error or (mode == "realtime" and latency >= 100) else action
            step = len(latencies)
            latencies.append(latency)
            game.step(applied)
            # Persistence is outside the response clock; rendering and encoding are inside it.
            (output / "frames" / f"{step:04d}.png").write_bytes(frame)
            ledger.append(
                {
                    "type": "step",
                    "step": step,
                    "nonce": nonce,
                    "frame_sha256": digest(frame),
                    "reply": reply,
                    "error": error,
                    "capture_started_ns": started,
                    "accepted_ns": accepted,
                    "latency_ms": latency,
                    "applied_action": applied,
                }
            )
            if aborted:
                break  # Kill/drain the transport; never accept a timed-out response on the next frame.
        measured = game.result()
        result = {
            "type": "result",
            "agent": agent_id,
            "game": game_id,
            "seed": seed,
            "mode": mode,
            "steps": len(latencies),
            "aborted": aborted,
            "game_result": measured,
            "score": 0.0 if aborted else measured["score"],
            "raw_score": measured["raw_score"],
            "latencies_ms": latencies,
            "errors": errors,
            "trust": "local-unattested",
            "version": __version__,
            "hardware": manifest["hardware"],
            "max_steps": max_steps,
            "latency_eligible": bool(latencies) and max(latencies) < 100 and not errors,
            "model": getattr(agent, "model", None),
            "provider_metadata": getattr(agent, "metadata", {}),
        }
        ledger.append(result)
        (output / "result.json").write_text(json.dumps(result, indent=2))
        return result
    finally:
        game.close()
        ledger.close()
