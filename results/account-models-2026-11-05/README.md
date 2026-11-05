# New account models with image input

Four newly accessible models completed the same 43-scenario suite on 5 November 2026.
Each scenario uses seed 3000 and at most eight decisions. The evaluator is 0.5.0.
These are short integration checks. They do not establish general game skill.
All results remain `local-unattested`. The official track has no entries.

| Model | Weighted / 100 | Quality / 100 | Suite p95 | Decisions | Errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| `claude-haiku-5-5` | 15.798 | 15.030 | 4.635 s | 340 | 1 |
| `gpt-6.1-terra` | 15.089 | 18.203 | 9.268 s | 342 | 0 |
| `gpt-6.1-sol` | 12.537 | 15.689 | 12.459 s | 344 | 0 |
| `claude-opus-5-5` | 9.005 | 7.323 | 5.855 s | 266 | 15 |

The score keeps 70% quality and 30% speed.
Speed is `100 / (1 + p95_ms / 1000)`.
The weighted score is `100 * (quality / 100)^0.7 * (speed / 100)^0.3`.
There is no hard latency cutoff. P95 uses every recorded response time, including failures, with linear interpolation.
The [validation](validation.json) recomputes quality, p95 and the geometric score independently.
The previous 16 weighted rows and their evidence remain unchanged.

## Account access

The [discovery](model-discovery.json) separates client menu entries from confirmed access.
A synthetic image call confirmed each selected model before the declaration.
The [preflight](model-preflight.json) contains sanitized access results.
It contains no game frames, account credentials or raw provider logs.
OpenAI's public model catalog returned HTTP 403 through the account token.
The successful Codex image calls confirmed access through the benchmark transport.

Claude Opus 5.5 first required a newer client. Claude Code was updated from 2.1.278 to 2.1.318.
Opus 5.5 and Haiku 5.5 then passed image access checks with explicit low effort.
Fable 5.1 returned HTTP 400 because the organization or workspace must enable data retention.
No account retention setting was changed. Fable has no scored run or leaderboard entry.
Claude Sonnet 5.5 was already on the board, so it was not repeated.

## Input and timing

Each turn uses the original full-frame PNG and the frozen `pixels-json-action/2` prompt.
The model returns one integer action. It receives no reward, state vector or action history.
Tools, MCP, slash commands and session persistence are disabled.
All four models use explicit low reasoning effort. Haiku 5.5 supports this setting; the old Haiku 4.5 run used its default effort.
The adapter does not retry a scored call, substitute a model or repair an invalid response. It uses no OCR or generated frame description.
The Mac runs one model and one game at a time. No scored call is run in parallel.

The host is an Apple M3 Max with 48 GiB RAM and 16 CPU cores, running macOS arm64.
Normal desktop work can share the host. Provider hardware is unknown.
Codex CLI is 0.166.0-alpha.5.1. Claude Code is 2.1.318.
A fresh authenticated CLI process handles each frame. Startup, frame encoding, transfer, inference and validation stay in the clock.
Game advancement is outside the clock. The simulation waits for each action.
The [runtime record](model-runtime.json) and each row identify these settings.
These are complete response-path times, not model-only inference times.
Jev uses a persistent direct image API. Local models keep their weights loaded. Those transport differences remain visible.

## Evidence

The [declaration](campaign.json) fixes the source hashes, suite, seed, horizon and model inventory before scoring.
The new run uses the same audited rebuilt game containers as the Jev run.
The [engine audit](../jev-image-2026-11-05/engine-rebuilds.json) records all nine changed image IDs.
All other task metadata matches the old hosted suite. Fixed prior traces matched 72 frames and nine native scores.
That audit does not establish equality for every trajectory. Each row keeps its actual engine IDs.

All 172 new episodes passed native replay. Every recorded failure stays in the suite.
A JSON parsing failure ends that episode. The referee records its failed response time and a replay placeholder; the episode earns zero quality.
Aborted episodes score zero. Natural termination can shorten an episode.
The export checks all retained ledger and PNG hashes and recomputes all 16 previous weighted rows.
It reuses their unchanged native replay reports. Historical source and recording rules stay archived.
Legacy latency flags in raw ledgers exist only for evidence compatibility. They impose no active limit.

- [Replay validation](replay-validation.json)
- [New evidence roots](new-evidence-roots.json)
- [All episodes](episodes.json)
- [Previous weighted snapshot](previous-snapshot.json)
- [Release evidence](https://github.com/DanielTea/generalgamebench/releases/tag/account-models-2026-11-05)

The release archive contains the new event ledgers, result records and original PNGs.
It contains no credentials, private paths, model weights or game binaries.
Hash checks and replay do not independently attest the original wall-clock times.
