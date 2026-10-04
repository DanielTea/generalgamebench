# Season 0 methodology

**Version:** 0.1.0. No official certified entries. The public board displays measured local/provisional results and a separate model exhibition.

## Response contract

Start a monotonic nanosecond timer immediately before the referee renders/encodes the observation. Include PNG encoding, nonce creation, JSON serialization, IPC or CLI startup, inference, JSON parsing and action validation. Stop at validated action receipt, before simulation advances. This is not photon-to-photon latency; display/compositor delay and the game response are not measured.

Strict eligibility requires **all recorded responses <100 ms**, zero protocol errors and no aborted episodes. Exactly 100 ms fails. p95 alone never grants eligibility. A finite sample cannot prove all future reactions will meet the deadline.

Image codecs are warmed before readiness for every baseline. Process startup and imports occur before the ready handshake and are excluded for persistent baseline processes. Model CLI startup is included on every decision; model exhibition timings must not be interpreted as raw provider inference latency. No selectively removed warmup observations.

Realtime simulation is **lockstep**, applying each accepted action for one native step or four Doom tics. It stops while the policy thinks. Late valid actions become wait; transport timeouts abort with zero score. Thus sub-100 ms qualification here measures the response path, not sustained 10 Hz service or continuous gameplay. A future realtime adapter must continue ticking independently and account for capture age, missed ticks and input acknowledgement.

## Scoring

Coin Run: `min(1, coins / (horizon / 6))`. Dodge Lanes: `max(0, 1 - hits / (horizon / 10))`. Bounds use a floor denominator of one. Doom uses the fixed ranges in `games.py`, clamped to [0,1]. These are task normalization anchors, not human-normalized scores. Always publish raw reward too.

Each seed contributes equally within a scenario; each scenario contributes equally to the suite aggregate. Changing the horizon, game list, interface, machine class or version defines a different comparison. Missing, duplicated, nonfinite or unexpected episodes are rejected. Aborted episodes remain with zero score. Sorting is descriptive only; overlapping confidence intervals do not establish meaningful differences. No official rank is assigned by the local summarizer.

95% percentile intervals use 2,000 bootstrap draws of seed blocks across the fixed scenarios, with a fixed analysis RNG. They describe seed variability, not model-training variability, machine variability, provider drift or future-task generalization. One seed gets no interval. Two seeds yield particularly weak uncertainty estimates.

## Evidence and verification

Every episode includes a referee manifest, every PNG observation, a hash-linked JSONL trace, nonces, monotonic timestamps, proposed/applied actions and a final result. `arena verify EPISODE` checks chain integrity, frame bytes, timing summaries and action legality, then recreates the same seeded game and recomputes frames and score. `arena rank` verifies episodes before summarizing the final ledger records; it does not trust a modified `result.json`.

Replays require the pinned dependencies and compatible renderer/platform. Pixel-perfect reproduction across different engine builds or architectures is not promised. Failure is explicit rather than silently accepting a differing replay.

Local development participants share the operator's machine. Their results remain `local-unattested`, even after deterministic replay. See SECURITY.md for the trust boundary and production admission requirements.

## First campaigns

Baselines: four original/reference policies × ten scenarios × ten seeds (1000–1009), horizon 80. Exhibition: Astra, Claude and reference policies × three scenarios × two seeds (2000–2001), horizon 8, separately labeled. Model provider errors found during integration are retained locally as failed setup attempts, excluded from the declared final campaign and disclosed in results provenance. No successful model gameplay attempts are selected for score.
