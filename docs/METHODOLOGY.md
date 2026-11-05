# Evaluation methodology

**Evaluator version:** 0.5.0. **Current scoring policy:** `quality70-speed30-p95-v1`.
There is no hard leaderboard latency limit. The recording version and the scoring policy are separate.
Earlier recordings retain their original evaluator versions.
All current results are local measurements without independent certification.
The official leaderboard has no entries.

## Response time

Start the monotonic timer before the referee requests the current game image.
Include image retrieval, PNG encoding, nonce creation, serialization, transport, inference, parsing and action validation.
Stop the timer when the referee accepts the validated action.
Exclude game advancement, renderer updates between decisions and evidence storage.
Display delay and the game's response to the action are not measured.

The leaderboard uses p95 as a continuous score component, with no pass/fail cutoff.
Pool every recorded response time from all declared games and seeds for one agent.
Include response times from failed and aborted episodes.
Do not calculate the mean of per-game or per-episode p95 values.
Do not remove slow samples or select successful retries.

Use NumPy's linear quantile method: `numpy.quantile(times, 0.95, method="linear")`.
For sorted samples, interpolate at index `0.95 * (sample_count - 1)`.
Use unrounded p95 in the weighted score.
The display can round p95 and the weighted score. Sorting uses the unrounded weighted score.
The complete sample distribution determines p95.
A finite test does not establish future response times.

Publish quality, weighted score, p50, p95 and maximum response time.
Also publish errors, aborted episodes and the number of decisions.
The current view has no `latency_eligible` or threshold-miss fields.
Errors and aborted episodes remain in the results. Aborted episodes score quality zero.
An incomplete suite has no aggregate result.
A weighted score does not establish valid replay, independent timing or official admission.

Warm image codecs before recording.
Persistent agent startup and model loading occur before readiness and stay outside the timer.
Per-frame model CLI startup stays inside the timer.
These different transports have different costs.
Keep them visible in each result.

Both modes use lockstep simulation. The game waits for the agent.
From version 0.5.0, both modes accept valid actions until the configured transport timeout.
The default timeout is 60 seconds. A timeout aborts the episode with score zero.
The transport timeout is separate from the continuous leaderboard score.
This keeps slow samples available for p95.
These results do not establish continuous real-time gameplay.

## Saved evidence

The current board derives its weighted score from saved quality and response times.
It does not change actions, quality, timing, failures, versions or trust status.
The former `suite-p95-200-v1` rule required suite p95 below 200 ms.
That cutoff was removed from the current leaderboard on 5 November 2026.
Historical snapshots and raw episode records retain those original flags for verification.
Versions 0.1.0 through 0.4.0 used a different rule: every response had to be below 100 ms.
Their realtime mode used a 100 ms deadline and replaced late actions with wait.
Those historical deadlines can affect both scores and recorded response times.
Do not compare those runs directly with new version 0.5.0 runs.
The evidence verifier uses the recorded version and policy.
Released ledgers and snapshots remain unchanged.

## Quality scoring

Coin Run: `min(1, coins / (horizon / 6))`. Dodge Lanes: `max(0, 1 - hits / (horizon / 10))`. Bounds use a floor denominator of one. Doom uses the fixed ranges in `games.py`, clamped to [0,1]. These are task normalization anchors, not human-normalized scores. Always publish raw reward too.

Each seed contributes equally within a scenario; each scenario contributes equally to the suite aggregate. Changing the horizon, game list, interface, machine class or version defines a different comparison. Missing, duplicated, nonfinite or unexpected episodes are rejected. Aborted episodes remain with zero score. Sorting is descriptive only; overlapping confidence intervals do not establish meaningful differences. No official rank is assigned by the local summarizer.

For `G` scenarios and `S` fixed seeds, the measured quality is `100 × sum(normalized_score[g,s]) / (G × S)`. For example, three scenario means of 0.8, 0.4 and 0 give 40/100. Normalization commonly uses `clip((raw - lower_anchor) / (upper_anchor - lower_anchor), 0, 1)`; success tasks use their declared success reward. The anchors are fixed before evaluation, never fitted to the observed models. Raw rewards remain in the episode evidence.

Equal scenario weights are not equal franchise weights: eight Doom and sixteen Procgen scenarios contribute eight and sixteen times the weight of a single scenario. A score is not an IQ measurement, a human-normalized skill estimate, or the percentage of games beaten. Some short survival tasks score highly even for an idle policy. The current weighted score combines this quality with continuous p95 responsiveness.

Normalization can also place a zero native reward above zero on the display scale. For example, Doom Basic's fixed anchors are -320 and 100, so a raw reward of 0 maps to about 76.2/100. This is why the raw reward, task rules and reference-policy controls matter when interpreting an aggregate.

95% percentile intervals use 2,000 bootstrap draws of seed blocks across the fixed scenarios, with a fixed analysis RNG. They describe seed variability, not model-training variability, machine variability, provider drift or future-task generalization. One seed gets no interval. Two seeds yield particularly weak uncertainty estimates.

## Weighted leaderboard score

The current policy is `quality70-speed30-p95-v1`.
Let `Q` be measured quality from 0 to 100 and `L` be the observed suite p95 in milliseconds.

```text
Speed = 100 / (1 + L / 1000)
Weighted = 100 × (Q / 100)^0.7 × (Speed / 100)^0.3
```

The 70/30 weights are a design choice, not an estimate learned from these models.
Quality receives the larger weight. Response time still has a visible effect.
The geometric mean keeps zero-quality agents at zero points, even if they respond instantly.
For positive quality, better quality or lower latency increases the score.
The score ranges from 0 to 100. It is not a percentage of games beaten.

The 1000 ms reference is fixed for every model and future run.
At p95 of 100 ms, the speed component is 90.91. At 1000 ms it is 50.
At 10000 ms it is 9.09. None of these values is a cutoff.
Adding a model cannot change another model's weighted score.
There is no normalization against the fastest or slowest current entry.

The table shows both components: measured quality and observed suite p95.
A game filter combines that game's quality with the same suite p95.
It does not substitute a per-game p95. This keeps the latency measurement consistent.
The `score` and `per_game` source fields retain their original quality meaning.
The new `weighted_score` and `weighted_per_game` fields identify the derived score.
Quality intervals remain quality intervals. A joint quality-and-latency interval has not been estimated.

Use the full response path, including network and command startup where applicable.
Different transport and image preparation paths remain visible in the run settings.
The weighted ranking describes measured system behavior. It is not a model-only inference comparison.
The [policy report](../results/weighted-score-2026-11-05/README.md) preserves the previous snapshot and validation.

## Evidence and verification

Every episode includes a referee manifest, every PNG observation, a hash-linked JSONL trace, nonces, monotonic timestamps, proposed/applied actions and a final result. `arena verify EPISODE` checks chain integrity, frame bytes, timing summaries and action legality, then recreates the same seeded game and recomputes frames and score. `arena rank` verifies episodes before summarizing the final ledger records; it does not trust a modified `result.json`.

Replays require the pinned dependencies and compatible renderer/platform. Pixel-perfect reproduction across different engine builds or architectures is not promised. Failure is explicit rather than silently accepting a differing replay.

Local development participants share the operator's machine. Their results remain `local-unattested`, even after deterministic replay. See SECURITY.md for the trust boundary and production admission requirements.

## Original Season 0 campaigns

Baselines: four original/reference policies × ten scenarios × ten seeds (1000–1009), horizon 80. Exhibition: Astra, Claude and reference policies × three scenarios × two seeds (2000–2001), horizon 8, separately labeled. Model provider errors found during integration are retained locally as failed setup attempts, excluded from the declared final campaign and disclosed in results provenance. No successful model gameplay attempts are selected for score.

## Expanded Mac exhibition

The expanded suite contains 33 fixed tasks. Hosted models are evaluated through existing authenticated CLI configurations; local VLMs use complete cached MLX snapshots and persistent loaded weights. All share the frozen pixels-json-action/2 prompt. Hosted processes start per frame, while local weights load before readiness, so latency includes different transport overheads. Up to ten hosted evaluations may run concurrently on the shared host alongside one local VLM; local VLMs run serially. These are end-to-end exhibition measurements, not isolated provider latency benchmarks.

Each model receives seed 3000 and an eight-decision horizon on every task. This very short single-seed suite receives no confidence interval and demonstrates integration only. Invalid model actions abort that episode with zero score and remain visible. Provider startup/access failures are reported separately and incomplete suites do not receive an aggregate rank. No best-of-attempt selection. Four reference policies use the same exhibition suite as controls. A separate local baseline track uses seeds 4000–4002 and horizon 24.

Optional task normalization, action restrictions, frame skip and licensing are detailed in [the runtime definitions](../environments/README.md). Library cards (Atari, Retro, PettingZoo) cover only their named validated task. The earlier experimental SuperTuxKart adapter was excluded from this historical cohort; the pinned native adapter was subsequently admitted in v0.3.

## Hosted-model refresh, 5 October 2026

The new cohort contains all 43 admitted scenarios, seed 3000 and eight decisions per scenario, using evaluator 0.4.0 and the unchanged pixels-json-action/2 prompt. It evaluates configured OpenAI and Anthropic models plus the explicitly requested `claude-opus-5-5` and `claude-sonnet-5-5` IDs. Four reference policies receive the same suite. Local VLMs remain available in the previous exhibition; they are not relabeled as new measurements.

The full campaign declaration, source hashes, model availability and replay reports are under [results/refresh-2026-10-05](../results/refresh-2026-10-05). Failed model replies count as zero-score episodes. Connection diagnostics are separate from scored gameplay. Resuming after a connection failure preserves the original failed episode and fills only missing scenarios; it never retries a scored episode to improve the result. Models without a complete verified suite receive no aggregate score.

The new and historical aggregates are separate because their scenario sets and evaluator versions differ. This remains a short integration exhibition, with no confidence interval and no certified ranks. Many tasks cannot reach a meaningful objective within eight decisions. A stronger skill comparison needs a separately declared campaign with longer task-appropriate horizons, more held-out seeds, and dedicated evaluation hardware.

[Season 0 methodology](METHODOLOGY_SEASON_0.md) and released evidence remain unchanged. New suites must never be pooled into the older scores.
