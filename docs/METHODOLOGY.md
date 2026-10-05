# Evaluation methodology

**Evaluator version:** 0.4.0. Historical cohorts retain their original versions. No official certified entries. The public board displays measured local/provisional results and a separate model exhibition.

## Response contract

Start a monotonic nanosecond timer immediately before the referee requests the current rendered observation. Engine advancement and eager renderer updates between decisions are outside the clock; snapshot retrieval and PNG encoding are inside it. Include PNG encoding, nonce creation, JSON serialization, IPC or CLI startup, inference, JSON parsing and action validation. Stop at validated action receipt, before simulation advances. This is not photon-to-photon latency; display/compositor delay and the game response are not measured.

Strict eligibility requires **all recorded responses <100 ms**, zero protocol errors and no aborted episodes. Exactly 100 ms fails. p95 alone never grants eligibility. A finite sample cannot prove all future reactions will meet the deadline.

Image codecs are warmed before readiness for every baseline. Process startup and imports occur before the ready handshake and are excluded for persistent baseline processes. Model CLI startup is included on every decision; model exhibition timings must not be interpreted as raw provider inference latency. No selectively removed warmup observations.

Realtime simulation is **lockstep**, applying each accepted action for one task-defined step (see the optional runtime definitions). It stops while the policy thinks. Late valid actions become wait; transport timeouts abort with zero score. Thus sub-100 ms qualification here measures the response path, not sustained 10 Hz service or continuous gameplay. A future realtime adapter must continue ticking independently and account for capture age, missed ticks and input acknowledgement.

## Scoring

Coin Run: `min(1, coins / (horizon / 6))`. Dodge Lanes: `max(0, 1 - hits / (horizon / 10))`. Bounds use a floor denominator of one. Doom uses the fixed ranges in `games.py`, clamped to [0,1]. These are task normalization anchors, not human-normalized scores. Always publish raw reward too.

Each seed contributes equally within a scenario; each scenario contributes equally to the suite aggregate. Changing the horizon, game list, interface, machine class or version defines a different comparison. Missing, duplicated, nonfinite or unexpected episodes are rejected. Aborted episodes remain with zero score. Sorting is descriptive only; overlapping confidence intervals do not establish meaningful differences. No official rank is assigned by the local summarizer.

For `G` scenarios and `S` fixed seeds, the displayed score is `100 × sum(normalized_score[g,s]) / (G × S)`. For example, three scenario means of 0.8, 0.4 and 0 give 40/100. Normalization commonly uses `clip((raw - lower_anchor) / (upper_anchor - lower_anchor), 0, 1)`; success tasks use their declared success reward. The anchors are fixed before evaluation, never fitted to the observed models. Raw rewards remain in the episode evidence.

Equal scenario weights are not equal franchise weights: eight Doom and sixteen Procgen scenarios contribute eight and sixteen times the weight of a single scenario. A score is not an IQ measurement, a human-normalized skill estimate, or the percentage of games beaten. Some short survival tasks score highly even for an idle policy. Latency does not alter exhibition scores; it is reported as a separate eligibility gate.

95% percentile intervals use 2,000 bootstrap draws of seed blocks across the fixed scenarios, with a fixed analysis RNG. They describe seed variability, not model-training variability, machine variability, provider drift or future-task generalization. One seed gets no interval. Two seeds yield particularly weak uncertainty estimates.

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
