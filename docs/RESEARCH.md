# Research and design rationale

Primary sources checked 2026-10-04. Recommendations below are our engineering synthesis, not claims that the sources endorse GeneralGameBench.

| Evidence / primary source | What it informs here |
| --- | --- |
| [BALROG](https://github.com/balrog-ai/BALROG) and [paper](https://arxiv.org/abs/2411.13543) | Diverse game environments reveal different agent skills. Fix the observation/action interface and disclose scaffolding; do not equate model names with complete agents. |
| [rliable](https://github.com/google-research/rliable) and [Statistical Precipice](https://arxiv.org/abs/2108.13264) | Report uncertainty and per-task distributions. The reference leaderboard uses equal-weight normalized means and paired seed-block bootstrap intervals. IQM, performance profiles and probability of improvement are recommended extensions, not implemented metrics. |
| [Procgen](https://github.com/openai/procgen) | Procedural variation and held-out levels help test generalization. Public development seeds and secret final seeds should be separated. Current seeds are public; no held-out generalization claim is made. |
| [ViZDoom](https://github.com/Farama-Foundation/ViZDoom) | A reproducible, fast 3D game environment with rendered observations and referee reward. Eight scenario adapters are executable today. |
| [MineRL](https://github.com/minerllabs/minerl) / [Malmo](https://github.com/microsoft/malmo) | Rich commercial-game research can use dedicated environments, but versions, game access and reproducible setup need explicit handling. |
| [SC2 API](https://github.com/Blizzard/s2client-api) / [PySC2](https://github.com/google-deepmind/pysc2) | APIs make controlled tasks possible, but state/features and pixels confer different advantages and require separate divisions. |
| [Unity ML-Agents](https://github.com/Unity-Technologies/ml-agents) | New modern 3D tasks can expose camera observations and a referee. An SDK cannot automatically integrate arbitrary commercial games. |
| [OpenAI Astra model](https://developers.openai.com/api/docs/models/gpt-6-astra) | Identifies the requested model and image-input support. Actual exhibition transport uses the user's authenticated Codex CLI. |
| [Claude vision](https://platform.claude.com/docs/en/build-with-claude/vision) | Images can be supplied as base64 PNG content blocks. Actual available account model resolved to Claude Opus 5. |

## Recommended leaderboard design

1. Define the unit of comparison as **agent + policy/scaffolding + model snapshot + hardware + task version + observation/action budget**. Pin and disclose all of them.
2. Publish per-game scores before promoting a broad aggregate. Keep pixels, structured-state, tool-enabled, realtime, and paused/lockstep play distinct.
3. Predeclare seeds and number of trials. Record every completed or failed scheduled episode; no selective removal of poor runs. Failures count as zero.
4. For single-player tasks, use native outcomes and fixed normalization anchors. For future head-to-head games, balance sides/maps and use a probabilistic rating with uncertainty (e.g. Bradley–Terry/TrueSkill), after enough opponents and matches. Do not fabricate Elo from solitary scores.
5. Measure reaction time on referee-owned monotonic clocks, from observation acquisition through validation. Publish all latency samples, p50/p95/max, deadline misses, warmup policy and network inclusion. Separate simulation time and wall time.
6. Keep final evaluation hidden and isolated. Submit agent artifacts, not claimed rewards. The referee owns seed generation, game state, inputs, score and evidence. Evaluate unseen layouts after submissions are frozen.
7. Sign evidence from independently operated evaluators, with keys outside the participant environment; maintain a trusted-key allowlist and append-only result storage. Hash chains alone do not authenticate a runner.
8. Require replay or independent adjudication, published disqualification reasons and an appeal path. Rotate holdout tasks without silently rewriting old seasons.
9. Make participation cheap: a tiny JSONL adapter, deterministic local suite, sample agents, container example, one command, an evidence bundle and an issue form. Never execute arbitrary submissions automatically on a privileged CI runner.

## Limits of this first season

Ten scenarios are not ten independent game engines: eight are Doom scenarios. Scores are strongly weighted toward Doom, and horizons are short. The two-seed model exhibition has little statistical power. Small variations must not be marketed as a robust model superiority result. Nothing here establishes a universal intelligence score, commercial-game mastery, or uncheatable execution.

A production service still needs isolated worker hosts, authenticated queues, quotas, model-access brokerage, licensed game installations, hardware pools, signed runs, reviewer operations and abuse testing. The published website is a static snapshot of actual measurements with a GitHub submission/review path.
