---
title: GeneralGameBench
colorFrom: red
colorTo: gray
sdk: static
app_file: index.html
fullWidth: true
license: mit
short_description: Game control tests with measured latency and replay evidence
tags:
  - leaderboard
  - gaming
  - games
  - domain:gaming
  - modality:image
  - modality:agent
  - eval:performance
  - submission:semiautomatic
  - test:public
  - judge:function
  - language:english
datasets:
  - {{dataset_id}}
pinned: true
---

# GeneralGameBench · Gaming agent leaderboard

GeneralGameBench tests agents that receive game images and return control actions.
The benchmark contains 43 scenarios in 2D, 3D, strategy, arcade and other game types.
The game catalog identifies tested tasks and proposed tasks.
Proposed commercial games do not contribute to the scores.

[Results Dataset](https://huggingface.co/datasets/{{dataset_id}}) ·
[Source code](https://github.com/DanielTea/generalgamebench) ·
[Test method](https://github.com/DanielTea/generalgamebench/blob/main/docs/METHODOLOGY.md) ·
[Replay evidence](https://github.com/DanielTea/generalgamebench/releases)

## Read the results

A Hugging Face Space is a hosted application.
This Space shows a fixed copy of the results.
Separate computers run the tests.
The results Dataset contains the same measurements in table format.

Each scenario converts its game reward to a score from 0 to 1.
The benchmark calculates the mean score across seeds for each scenario.
It then calculates the mean across scenarios and multiplies this value by 100.
An aborted episode receives zero points.
An incomplete suite does not receive a total score.

Compare results only when the suite IDs, seeds, test duration, task versions and hardware are the same.
The latency limit is separate from the score.
The **suite p95 must be below 200 ms**. Exactly 200 ms fails.
The calculation pools all recorded response times, including failed episodes.
It uses linear interpolation. It does not average per-game p95 values.
Errors and aborted episodes stay visible. A latency pass does not grant an official rank.
The timer includes image retrieval, encoding, transport, inference and action validation.
The simulation waits between actions.
These tests do not prove continuous real-time control.

The leaderboard shows the current model tests and official ranks.
The current hosted-model tests use one seed and eight decisions per scenario.
These short tests show that the connections work.
They do not give a reliable measure of model intelligence.
All current results come from local tests without independent certification.
The official leaderboard has no entries.

## Submit an agent

The submission process is semiautomatic.
You run the tests and send the evidence for review.
The maintainers examine the evidence before they accept the results.

1. Start Docker.
2. Run these commands:

```sh
git clone https://github.com/DanielTea/generalgamebench
cd generalgamebench
./ggbench
```

3. Open `runs/submission/SUBMIT.txt`.
4. Follow the submission instructions in that file.
5. Attach the evidence to a [benchmark submission](https://github.com/DanielTea/generalgamebench/issues/new?template=submission.yml).

The portable suite contains 10 scenarios and 50 episodes.
It replays each result for verification.
See the [agent instructions](https://github.com/DanielTea/generalgamebench/blob/main/docs/SUBMISSIONS.md) for the full procedure.
A submission does not automatically receive an official rank.
This Space does not run submitted agent code or receive provider credentials.

## Finder category and licenses

The metadata follows the [Leaderboard Finder](https://huggingface.co/spaces/OpenEvals/find-a-leaderboard) format.
The proposed tag `domain:gaming` identifies the new Gaming category.
The Finder requires at least five community likes and maintainer approval.
Publication of this Space does not confirm inclusion in the Finder.

The original code uses the MIT license.
Game media keeps its original licenses and credits.
See the [media notices](media/NOTICE.txt) and [asset sources](media/sources.json).
The Dataset contains measurements and test details.
It does not contain game images or model weights.
After publication, `publication.json` identifies the Dataset commit and the snapshot checksum.
