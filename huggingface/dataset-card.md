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

The `score_100` column gives the normalized game score.
The `suite_score_100` column gives the mean score across the complete suite.
The calculation first averages seeds within each scenario.
It then averages scenarios with equal weight.
An aborted episode receives zero points.

Columns with the `suite_` prefix describe the complete campaign.
These columns include timing, confidence intervals, episode counts, decision counts and errors.
The export repeats these values on each game row.
The field `latency_eligible` is true when the complete suite p95 is below 200 ms.
Exactly 200 ms fails. The calculation uses all recorded response times and linear interpolation.
The fields `latency_policy_id` and `latency_limit_ms` identify this rule.
The field `suite_misses` counts responses at or above 200 ms.
Errors and aborted episodes do not change this latency test. They remain in the scores and error counts.
Do not add these values across rows.
Do not interpret them as measurements for individual games.

Compare only rows with the same `suite_id`.
Also examine `mode`, `transport`, task details, model revision and prompt version.
The suite ID includes games, seeds, decision limits, evaluator versions, task versions and hardware conditions.
A null seed list or model revision means that the source did not record this value.
Some reference policies do not have a model ID.

The `task_metadata_json` and `provider_metadata_json` columns contain JSON strings.
This format keeps engine and provider details without changes to the Dataset viewer column types.
The root JSONL files retain the original nested objects.
The files in `viewer/` supply the Dataset viewer.

## Test limits

This benchmark measures visual game control within fixed limits.
It does not measure intelligence in full.
The current vision model tests run on a Mac.
They use one seed and a limit of eight decisions per scenario.
Each model uses pinned weights from Hugging Face.
The archive keeps the previous results and their recording rules.
Many games only start during these short tests.
Do not use these results as a reliable ranking of model intelligence.

Different tests can use different games, durations, seeds and hardware.
The `trust` column retains the source's local test status.
A suite p95 below 200 ms does not prove independent verification.
This Dataset does not give official ranks.
Public seeds and local execution do not prove protection against cheating.
See the [security model](https://github.com/DanielTea/generalgamebench/blob/main/SECURITY.md).

Separate test computers produce the results.
The maintainers review the evidence before publication.
Contributors use the [submission procedure](https://github.com/DanielTea/generalgamebench/blob/main/docs/SUBMISSIONS.md).
This Dataset does not contain personal data, provider credentials, game images or model weights.
The original measurements and export code use the MIT license.
Third-party engines, models and media keep their original licenses.
