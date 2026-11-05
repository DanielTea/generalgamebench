# Continuous quality and response-time score

The leaderboard now uses policy `quality70-speed30-p95-v1`.
It gives quality 70% weight and speed 30% weight with a geometric mean.
There is no hard latency cutoff and no pass/fail latency badge.

```text
Speed = 100 / (1 + suite_p95_ms / 1000)
Weighted = 100 × (quality / 100)^0.7 × (speed / 100)^0.3
```

Quality remains the original scenario-balanced score from 0 to 100.
The geometric mean gives zero points to zero-quality agents, even if they are fast.
For positive quality, higher quality or lower p95 increases the score.
The 1000 ms reference is a scale, not a deadline.
It maps 100 ms to speed 90.91, 1000 ms to 50, and 10000 ms to 9.09.
It stays fixed when models are added. No scores depend on the fastest current model.

## Why this weighting

The weights express a design choice: useful actions matter more than speed alone,
but response time must affect the ranking of a system that acts on game images.
A linear sum can give a fast zero-quality agent substantial points.
The geometric mean prevents that result while allowing a continuous tradeoff.
The reference and weights are explicit so later policy changes can use a new version.
They are not estimates of model intelligence or a statistically calibrated utility function.

## Recalculated standings

| Model | Weighted / 100 | Quality / 100 | Suite p95 |
| --- | ---: | ---: | ---: |
| `jev-1.14.0` | 26.765 | 17.474 | 381.54 ms |
| `LiquidAI/LFM2.5-VL-450M-MLX-4bit` | 20.265 | 12.718 | 663.88 ms |
| `claude-sonnet-5` | 20.043 | 17.757 | 2761.46 ms |
| `claude-opus-5[1m]` | 19.473 | 17.998 | 3273.09 ms |
| `claude-sonnet-5-5` | 15.474 | 14.176 | 4268.19 ms |
| `gpt-5.5` | 13.549 | 17.344 | 12131.92 ms |
| `gpt-5.6-terra` | 13.011 | 17.992 | 15372.74 ms |
| `gpt-6-astra` | 12.503 | 18.125 | 18023.87 ms |
| `gpt-6-sol` | 11.976 | 15.703 | 14712.85 ms |
| `gpt-5.6-luna` | 11.526 | 14.437 | 13674.89 ms |
| `gpt-5.6-sol` | 11.384 | 15.323 | 16570.74 ms |
| `gpt-6-luna` | 10.972 | 15.030 | 17991.21 ms |
| `claude-haiku-4-5-20251001` | 10.374 | 13.201 | 15912.67 ms |
| `mlx-community/SmolVLM2-256M-Video-Instruct-mlx` | 1.010 | 0.211 | 1565.56 ms |
| `mlx-community/FastVLM-0.5B-bf16` | 0.000 | 0.000 | 1429.31 ms |
| `mlx-community/SmolVLM2-500M-Video-Instruct-mlx` | 0.000 | 0.000 | 1982.70 ms |

The table uses the published quality values and unrounded observed suite p95.
Sorting uses the unrounded weighted score. The page rounds it to two decimal places.
Ties share a rank. Component quality and p95 remain visible.
Game filters use game quality and the same observed suite p95, not a per-game p95.
Quality confidence intervals remain quality intervals; no weighted-score interval is claimed.

## Preservation and validation

This is a scoring-view update, with zero new model or game calls.
The [previous snapshot](previous-snapshot.json) preserves the quality-only ordering and old latency flags.
All quality values, response times, errors, seeds, task settings, versions and trust status stay unchanged.
Existing episode ledgers, game frames, campaign reports and release archives are not rewritten.
Historical threshold fields remain only in original evidence and explicitly named recording metadata.
The current active rows contain no latency eligibility or threshold-miss fields.

The [validation report](validation.json) binds the previous snapshot by SHA-256 and lists every derived result.
The source `score` and `per_game` fields continue to mean measured quality.
New weighted fields identify the derived score. The current Hugging Face schema is version 2.

All current entries remain local-unattested. The official track stays empty.
These tests use one seed and up to eight decisions per scenario; they cannot establish model skill.
End-to-end p95 includes each model's actual capture, preprocessing and transport path.
Native API requests, fresh command calls and persistent local inference have different costs.
The weighted ranking therefore describes measured system behavior, not model-only inference speed.
