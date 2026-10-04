"""Balanced scenario scores and paired-seed bootstrap intervals, not invented Elo."""

import math
from collections import defaultdict

import numpy as np


def summarize(
    results: list[dict], games: list[str], seeds: list[int], bootstraps=2000
) -> list[dict]:
    if not games or not seeds or len(set(games)) != len(games) or len(set(seeds)) != len(seeds):
        raise ValueError("Games and seeds must be unique and nonempty")
    groups = defaultdict(list)
    for row in results:
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
                "games": games,
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
                "model": rows[0].get("model"),
                "provider_metadata": rows[-1].get("provider_metadata", {}),
            }
        )
    return sorted(board, key=lambda x: (-x["score"], x["agent"]))
