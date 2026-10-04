"""Hash-linked referee evidence; integrity checks are not runner authentication."""

import hashlib
import json
import math
from pathlib import Path


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Ledger:
    def __init__(self, path: Path):
        self.file = path.open("x")
        self.previous, self.sequence = "0" * 64, 0

    def append(self, payload: dict):
        row = {"sequence": self.sequence, "previous": self.previous, "payload": payload}
        row["hash"] = digest(canonical(row))
        self.file.write(json.dumps(row, separators=(",", ":")) + "\n")
        self.file.flush()
        self.previous, self.sequence = row["hash"], self.sequence + 1

    def close(self):
        self.file.close()


def read_ledger(path: Path) -> list[dict]:
    previous, payloads = "0" * 64, []
    for i, line in enumerate(path.read_text().splitlines()):
        row = json.loads(line)
        claimed = row.pop("hash")
        if row["sequence"] != i or row["previous"] != previous or digest(canonical(row)) != claimed:
            raise ValueError(f"Evidence chain broken at record {i}")
        previous = claimed
        payloads.append(row["payload"])
    if (
        not payloads
        or payloads[0].get("type") != "manifest"
        or payloads[-1].get("type") != "result"
    ):
        raise ValueError("Incomplete episode evidence")
    return payloads


def verify_episode(directory: Path, replay: bool = True) -> dict:
    from .games import make_game
    from .protocol import validate_reply

    rows = read_ledger(directory / "events.jsonl")
    manifest, result = rows[0], rows[-1]
    events = rows[1:-1]
    if manifest.get("mode") not in {"realtime", "exhibition"}:
        raise ValueError("Unknown evaluation mode")
    for key in ("agent", "game", "seed", "max_steps", "mode", "hardware", "version", "trust"):
        if result[key] != manifest[key]:
            raise ValueError("Manifest/result mismatch")
    if not events or len(events) > manifest["max_steps"]:
        raise ValueError("Invalid episode length")
    if any(e.get("type") != "step" for e in events):
        raise ValueError("Unexpected evidence record")
    game = make_game(manifest["game"], manifest["seed"], manifest["max_steps"]) if replay else None
    try:
        if manifest.get("game_metadata", {}) != result.get("game_metadata", {}):
            raise ValueError("Game metadata mismatch")
        if game and manifest.get("game_metadata") != getattr(game, "metadata", None):
            # Empty metadata is the original native/Doom format.
            if manifest.get("game_metadata") or getattr(game, "metadata", None):
                raise ValueError("Replay engine or task version differs")
        seen_nonces = set()
        prior_time = -1
        for i, event in enumerate(events):
            if event["step"] != i:
                raise ValueError("Non-contiguous steps")
            frame = (directory / "frames" / f"{i:04d}.png").read_bytes()
            if digest(frame) != event["frame_sha256"]:
                raise ValueError("Frame digest mismatch")
            if game and digest(game.frame()) != event["frame_sha256"]:
                raise ValueError("Deterministic replay frame mismatch")
            if not event["error"]:
                validate_reply(
                    event["reply"], {"nonce": event["nonce"], "actions": manifest["actions"]}
                )
            elapsed = (event["accepted_ns"] - event["capture_started_ns"]) / 1e6
            if (
                not math.isfinite(event["latency_ms"])
                or elapsed < 0
                or abs(elapsed - event["latency_ms"]) > 1e-6
            ):
                raise ValueError("Timing mismatch")
            if event["capture_started_ns"] < prior_time or event["nonce"] in seen_nonces:
                raise ValueError("Reused observation or nonmonotonic clock")
            prior_time = event["accepted_ns"]
            seen_nonces.add(event["nonce"])
            if event["error"] and i != len(events) - 1:
                raise ValueError("Episode continued after transport failure")
            expected = (
                0
                if event["error"] or (manifest["mode"] == "realtime" and elapsed >= 100)
                else event["reply"]["action"]
            )
            if event["applied_action"] != expected:
                raise ValueError("Illegal applied action")
            if game:
                game.step(expected)
        if len(events) != result["steps"]:
            raise ValueError("Result step count mismatch")
        errors = [e["error"] for e in events if e["error"]]
        times = [e["latency_ms"] for e in events]
        if result["errors"] != errors or result["latencies_ms"] != times:
            raise ValueError("Result timing/errors do not match evidence")
        if result["aborted"] != bool(errors):
            raise ValueError("Incorrect abort status")
        if result["latency_eligible"] != (max(times) < 100 and not errors):
            raise ValueError("Incorrect latency eligibility")
        expected_score = 0.0 if errors else result["game_result"]["score"]
        if (
            result["score"] != expected_score
            or result["raw_score"] != result["game_result"]["raw_score"]
        ):
            raise ValueError("Result score does not match referee")
        if game and game.result() != result["game_result"]:
            raise ValueError("Referee score mismatch")
        if game and not game.done and not result["aborted"]:
            raise ValueError("Premature episode completion")
        return {
            "valid": True,
            "steps": len(events),
            "replayed": replay,
            "authentication": "local-unattested",
        }
    finally:
        if game:
            game.close()
