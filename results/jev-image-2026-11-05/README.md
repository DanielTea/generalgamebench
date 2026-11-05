# Jev 1.14 with native image input

Jev 1.14.0 completed all 43 scenarios on 5 November 2026.
The latest alias resolved to `jev-1.14.0` in the [authenticated image preflight](model-preflight.json).
The [campaign declaration](campaign.json) pins that version and 111 source checksums.
The evaluator is 0.5.0. Each scenario uses seed 3000 and a limit of eight decisions.
The run contains 43 episodes and 342 decisions, with no errors or aborted episodes.
Natural game termination can shorten an episode.

| Metric | Measured result |
| --- | ---: |
| Score / 100 | 17.474 |
| Model exhibition position | 5 of 16 |
| Suite p50 | 197.74 ms |
| Suite p95 | 381.54 ms |
| Suite maximum | 639.60 ms |
| Responses at or above 200 ms | 159 |
| Errors / aborted episodes | 0 / 0 |

The suite p95 exceeds the 200 ms limit. Jev fails this latency test.
Exactly 200 ms also fails. The score remains separate from the latency result.
All 342 response times contribute to the linearly interpolated p95.
The [validation report](validation.json) independently checks the score, response times and counts.
One seed gives no confidence interval. These short runs check integration; they cannot establish model skill.
All results remain `local-unattested`. The official leaderboard has no entries.

## Native images and decisions

The model receives the rendered PNG frame and the fixed `pixels-json-action/2` prompt.
A native Choice question provides the same allowed integer action options.
The adapter maps the returned choice to the referee's action index.
There is no OCR, generated scene description, game-state vector, action history or tool use.
The model does not receive the game seed, coordinates or reward.

TypeSafe requires at least 280 pixels on each side.
The adapter applies integer nearest-neighbor upscaling only when a frame is too small.
It repeats existing pixels and preserves the full frame and aspect ratio.
It performs no crop or downsampling. Larger frames remain unchanged.
The saved evidence retains the original frame; the frozen adapter reproduces the submitted image.
The [image preparation code](../../src/generalgamebench/jev.py) and provider metadata identify this step.
Its decoding, upscaling and PNG encoding remain inside the measured response clock.

The Mac runs one model and one game at a time.
The host is an Apple M3 Max with 48 GiB RAM and 16 CPU cores.
Jev uses direct HTTPS multipart image requests and a persistent connection.
The adapter opens a new connection after five seconds without a request.
Three uniform gray startup images precede scoring. They use the same image preparation.
The clock includes capture, encoding, transfer, provider inference, parsing and action validation.
Game advancement occurs outside the clock. The simulation waits for each action.
No scored request was retried. All scored failures would remain in the results.
The [preflight notes](api-preflight-notes.json) retain two unscored image-dimension rejections before the declaration.
No API key, account credentials or provider response body is included in public evidence.

Earlier hosted models start a fresh command process for each image.
Local MLX models retain their weights in memory.
The table retains each model's transport and startup conditions.
These timings measure the complete response path, not model-only inference.

## Rebuilt engines and replay evidence

Nine Docker images were missing and were rebuilt from the existing pinned engine sources and patches.
Their container image IDs changed. All other task metadata matches the earlier runs.
The [rebuild audit](engine-rebuilds.json) checks one fixed prior eight-action trace per scenario.
All 72 camera frames and all nine native scores match exactly.
This audit does not establish equivalence for every possible trajectory.
Each new result retains its actual rebuilt container image ID.

All 43 new episodes passed exact native frame, action and score replay before publication.
The exporter checks source hashes before and after replay.
It also checks each result file against its event ledger, image hashes and declared settings.
The [evidence roots](new-evidence-roots.json) identify the new episode ledgers.
The [release](https://github.com/DanielTea/generalgamebench/releases/tag/jev-image-2026-11-05)
contains these ledgers, original PNG frames and results.
The [source tag](https://github.com/DanielTea/generalgamebench/tree/jev-image-2026-11-05-source)
identifies the implementation recorded in the declaration.
Use the [Jev run procedure](../../docs/JEV.md) to reproduce the API integration.

The previous 15 model rows remain unchanged in the [previous snapshot](previous-snapshot.json).
Their 645 episode ledgers, image checksums and rankings were checked again.
Their saved native replay proofs remain in the [retained evidence report](retained-evidence.json).
Earlier replay files remain in the [prior release](https://github.com/DanielTea/generalgamebench/releases/tag/hosted-rerun-2026-10-05).
The combined table contains 688 episodes and 4,550 decisions.
The public page and Hugging Face export keep the current model exhibition and official view.
They do not restore removed baseline or previous-result views.
