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
  - 1K<n<10K
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
The `local_previous` and `exhibition_previous` configurations contain results from earlier tests.
Do not combine these results with current tests.

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
The current hosted-model tests use one seed and eight decisions per scenario.
Many games only start during these short tests.
Do not use these results as a reliable ranking of model intelligence.

Previous tests and local policies can use different games, durations, seeds and hardware.
The `trust` column retains the source's local test status.
A response below 100 ms does not prove independent verification.
This Dataset does not give official ranks.
Public seeds and local execution do not prove protection against cheating.
See the [security model](https://github.com/DanielTea/generalgamebench/blob/main/SECURITY.md).

Separate test computers produce the results.
The maintainers review the evidence before publication.
Contributors use the [submission procedure](https://github.com/DanielTea/generalgamebench/blob/main/docs/SUBMISSIONS.md).
This Dataset does not contain personal data, provider credentials, game images or model weights.
The original measurements and export code use the MIT license.
Third-party engines, models and media keep their original licenses.
