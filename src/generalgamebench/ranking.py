"""Balanced scenario scores and paired-seed bootstrap intervals, not invented Elo."""

import json
import math
from collections import defaultdict

import numpy as np


def summarize(
    results: list[dict], games: list[str], seeds: list[int], bootstraps=2000
) -> list[dict]:
    if not games or not seeds or len(set(games)) != len(games) or len(set(seeds)) != len(seeds):
        raise ValueError("Games and seeds must be unique and nonempty")
    groups = defaultdict(list)
    task_metadata = {}
    cohorts = {(r["mode"], r["hardware"], r["version"], r["max_steps"]) for r in results}
    if len(cohorts) > 1:
        raise ValueError("A leaderboard must use one mode, hardware, version and horizon")
    for row in results:
        identity = json.dumps(row.get("game_metadata", {}), sort_keys=True)
        if row["game"] in task_metadata and task_metadata[row["game"]] != identity:
            raise ValueError("Mixed engine or task versions")
        task_metadata[row["game"]] = identity
        if not math.isfinite(row["score"]) or not 0 <= row["score"] <= 1:
            raise ValueError("Invalid normalized score")
        if not row["latencies_ms"] or any(
            not math.isfinite(x) or x < 0 for x in row["latencies_ms"]
        ):
            raise ValueError("Missing or invalid timing")
        groups[
            (row["agent"], row["mode"], row["hardware"], row["version"], row["max_steps"])
        ].append(row)
    board = []
    expected = {(g, s) for g in games for s in seeds}
    for (agent, mode, hardware, version, max_steps), rows in groups.items():
        identities = {
            json.dumps(
                {
                    "model": r.get("model"),
                    **{
                        k: r.get("provider_metadata", {}).get(k)
                        for k in ("requested_model", "revision", "prompt_version", "transport")
                    },
                },
                sort_keys=True,
            )
            for r in rows
        }
        if len(identities) != 1:
            raise ValueError("Mixed model, prompt, transport or weight revisions")
        indexed = {}
        for row in rows:
            key = (row["game"], row["seed"])
            if key in indexed:
                raise ValueError(f"Duplicate episode for {agent}: {key}")
            indexed[key] = row
        if set(indexed) != expected:
            raise ValueError(f"Incomplete or unexpected suite for {agent}")
        matrix = np.array([[indexed[g, s]["score"] for s in seeds] for g in games])
        rng = np.random.default_rng(2026)
        # Resample seed blocks jointly across games; games have equal fixed weight.
        samples = rng.integers(0, len(seeds), size=(bootstraps, len(seeds)))
        values = matrix[:, samples].mean(axis=(0, 2)) * 100
        ci = np.quantile(values, [0.025, 0.975]).tolist() if len(seeds) >= 2 else None
        times = np.array([t for row in rows for t in row["latencies_ms"]])
        eligible = bool(np.max(times) < 100) and all(
            not r["errors"] and not r["aborted"] for r in rows
        )
        board.append(
            {
                "agent": agent,
                "mode": mode,
                "hardware": hardware,
                "version": version,
                "max_steps": max_steps,
                "score": round(float(matrix.mean() * 100), 3),
                "ci95": ci,
                "episodes": len(rows),
                "seeds": len(seeds),
                "seed_ids": seeds,
                "games": games,
                "task_metadata": {g: json.loads(task_metadata[g]) for g in games},
                "decisions": len(times),
                "p50_ms": float(np.median(times)),
                "p95_ms": float(np.quantile(times, 0.95)),
                "max_ms": float(np.max(times)),
                "misses": int(np.sum(times >= 100)),
                "latency_eligible": eligible,
                "trust": "local-unattested",
                "official_rank": None,
                "per_game": {
                    g: round(float(matrix[i].mean() * 100), 3) for i, g in enumerate(games)
                },
                "errors": sum(len(r["errors"]) for r in rows),
                "aborted_episodes": sum(bool(r["aborted"]) for r in rows),
                "model": rows[0].get("model"),
                "provider_metadata": rows[-1].get("provider_metadata", {}),
            }
        )
    return sorted(board, key=lambda x: (-x["score"], x["agent"]))
