---
pretty_name: GeneralGameBench game control results
license: mit
language:
  - en
tags:
  - evaluation
  - leaderboard
  - gaming
  - games
  - game-ai
  - reinforcement-learning
size_categories:
  - {{size_category}}
configs:
{{configs}}
---

# GeneralGameBench test results

[Leaderboard](https://huggingface.co/spaces/{{space_id}}) ·
[Source code](https://github.com/DanielTea/generalgamebench) ·
[Test method](https://github.com/DanielTea/generalgamebench/blob/main/docs/METHODOLOGY.md) ·
[Replay evidence](https://github.com/DanielTea/generalgamebench/releases)

This Dataset contains test results.
Each row gives one agent's score for one game in a fixed test campaign.
All measurements come from the GeneralGameBench result snapshot.
The export does not add artificial scores.

| Configuration | Agent/game rows |
| --- | ---: |
{{counts}}

Empty result groups have no configuration or rows.
The official leaderboard is currently empty.
This Dataset contains the current model exhibition.

## Load the data

Use this example to load the current model results:

```python
from datasets import load_dataset

rows = load_dataset("{{dataset_id}}", "exhibition", split="test")
```

Set `revision` to a commit ID to use a fixed version.
The Space records its matching Dataset commit in `publication.json`.
The Dataset file `snapshot.json` is identical to the Space file `data.json`.
Its SHA-256 checksum is `{{snapshot_sha256}}`.

## Column definitions

The primary score is `suite_weighted_score_100`.
It uses 70% quality and 30% speed with a weighted geometric mean.
Speed is `100 / (1 + suite_p95_ms / 1000)`.
The score is `100 × (quality / 100)^0.7 × (speed / 100)^0.3`.
The reference is fixed; there is no hard latency cutoff.
Zero quality always gives zero weighted score.

`quality_score_100` is the normalized game quality.
`suite_quality_score_100` is the mean quality across the complete suite.
`score_100` and `suite_score_100` remain aliases for those quality values.
`weighted_score_100` combines game quality with the same observed suite p95.
The benchmark first averages quality across seeds within each scenario,
then averages scenarios with equal weight. Aborted episodes receive quality zero.

Schema version 2 removes active latency eligibility, cutoff and threshold-miss columns.
`scoring_policy_id`, `quality_weight`, `speed_weight` and `latency_reference_ms` identify the formula.
The original recordings and older Dataset revisions keep their historical metadata.

Columns with the `suite_` prefix describe the complete campaign.
They include quality, weighted score, response time, counts and quality confidence intervals.
The export repeats these values on each game row.
The p95 calculation uses all recorded response times and linear interpolation.
Quality intervals do not estimate uncertainty in the weighted score.
Do not add these values across rows.
Do not interpret them as measurements for individual games.

Compare only rows with the same `suite_id`.
Also examine `mode`, `transport`, task details, model revision and prompt version.
The suite ID includes games, seeds, decision limits, evaluator versions, task versions, hardware conditions and the scoring policy ID.
A null seed list or model revision means that the source did not record this value.
Some reference policies do not have a model ID.

The `task_metadata_json` and `provider_metadata_json` columns contain JSON strings.
This format keeps engine and provider details without changes to the Dataset viewer column types.
The root JSONL files retain the original nested objects.
The files in `viewer/` supply the Dataset viewer.

## Test limits

This benchmark measures visual game control within fixed limits.
It does not measure intelligence in full.
The Mac runs the current game tests.
They use one seed and a limit of eight decisions per scenario.
Local vision models use pinned weights from Hugging Face.
OpenAI and Anthropic models use their hosted services.
Each OpenAI or Anthropic action starts a new command process. Its timing includes network time and command startup.
Jev uses native image input, Choice output and a persistent direct HTTPS connection.
Small frames use integer nearest-neighbor upscaling to meet the API minimum of 280 pixels per side.
This image preparation time remains in the response clock. The full frame and aspect ratio are preserved.
Jev uses nine rebuilt containers from the same pinned engine sources. Their actual image IDs remain in the data.
One fixed camera and native-score trace per rebuilt scenario passed exact replay.
The [Jev report](https://github.com/DanielTea/generalgamebench/tree/main/results/jev-image-2026-11-05) records these differences.
The models share the same task definitions. Their inference paths differ.
The suite ID keeps these test conditions distinct. This table does not measure model-only speed.
The archive keeps the previous results and their recording rules.
Many games only start during these short tests.
Do not use these results as a reliable ranking of model intelligence.

Different tests can use different games, durations, seeds and hardware.
The `trust` column retains the source's local test status.
A weighted score does not prove independent verification.
This Dataset does not give official ranks.
Public seeds and local execution do not prove protection against cheating.
See the [security model](https://github.com/DanielTea/generalgamebench/blob/main/SECURITY.md).

Separate test computers produce the results.
The maintainers review the evidence before publication.
Contributors use the [submission procedure](https://github.com/DanielTea/generalgamebench/blob/main/docs/SUBMISSIONS.md).
This Dataset does not contain personal data, provider credentials, game images or model weights.
The original measurements and export code use the MIT license.
Third-party engines, models and media keep their original licenses.
