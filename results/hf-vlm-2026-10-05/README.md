# Vision model tests on the Mac

This campaign uses four vision models with pinned weights from Hugging Face.
The Mac runs the models and the full 43-scenario suite. Hugging Face hosts the
result page and Dataset. It does not run this campaign.

| Model | Weight format |
| --- | --- |
| SmolVLM2 256M Video Instruct | MLX |
| SmolVLM2 500M Video Instruct | MLX |
| LFM2.5-VL 450M | MLX 4-bit |
| FastVLM 0.5B | MLX BF16 |

The [model inventory](model-inventory.json) gives each source URL and commit.
The [campaign declaration](campaign.json) gives the source checksums and test settings.

## Measured results

All four models completed the declared 43-scenario suite. None passed the latency test.

| Model | Score / 100 | Suite p95 | Reply errors | Recorded decisions |
| --- | ---: | ---: | ---: | ---: |
| LFM2.5-VL 450M, 4-bit | 12.718 | 663.88 ms | 1 | 337 |
| SmolVLM2 256M | 0.211 | 1565.56 ms | 41 | 57 |
| FastVLM 0.5B, BF16 | 0.000 | 1429.31 ms | 42 | 50 |
| SmolVLM2 500M | 0.000 | 1982.70 ms | 43 | 43 |

The suite contains 172 episodes and 487 recorded decisions. The results retain
all 127 reply errors. An error ends its episode. A completed suite can contain
aborted episodes. The latency test uses the unrounded values in the result files.

## Test conditions

The host is an Apple M3 Max with 48 GiB of memory and 16 CPU cores.
Only one model and one game run at a time. The model weights stay in memory
between games. A model restart receives the same startup procedure.

Before scored actions, the model receives three uniform gray images.
Their sizes are 160 by 120, 320 by 240, and 960 by 640 pixels.
These images contain no game data. The startup prompt tells the model to wait.
Startup time is separate from the response measurements.
Every game call remains in the measurements, including compilation delays.

All models use prompt `pixels-json-action/2`. They receive only the game image,
the task instructions, and the permitted actions. They must return the required
JSON action. The adapter does not convert other text into an action.
A reply error ends the episode and gives it zero points.
The archive keeps the failed reply and its measured response time.

Each scenario uses seed 3000 and a limit of eight decisions.
The referee records each episode and immediately checks its native replay.
The exporter checks the replay again before publication.
It rejects missing episodes, changed source files, and mixed task versions.
These short tests check model integration. They cannot establish model skill.

## Latency and evidence

The latency test uses all recorded response times from the complete suite.
It calculates p95 with linear interpolation. A value below 200 ms passes.
Exactly 200 ms fails. Scores, errors, and trust status remain separate.
The timer includes image retrieval, encoding, transfer, inference, and action
validation. The game waits for each action. Engine advancement is outside this timer.

The model table shows only this new verified cohort. SuperTuxKart uses task
version 3 and renderer `deterministic-render-v2`. Earlier results use different
renderer settings. Do not combine those results with this cohort.

The [previous snapshot](previous-snapshot.json) retains the earlier result data
without changes. The new snapshot records its SHA-256 checksum.
Earlier campaign directories and release files retain their original evidence
and recording rules. The official leaderboard remains empty.

Use [the release files](https://github.com/DanielTea/generalgamebench/releases/tag/hf-vlm-2026-10-05)
to obtain the new images and action records. The result Dataset contains
measurements and metadata. It contains no model weights or game images.
