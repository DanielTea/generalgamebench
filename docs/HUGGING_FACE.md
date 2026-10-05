# Hugging Face publication

The [Space](https://huggingface.co/spaces/danieltee/generalgamebench) shows the leaderboard.
The [Dataset](https://huggingface.co/datasets/danieltee/generalgamebench-results) contains the measured results.
Separate computers run the games and evaluate the agents.
The Space does not execute submitted code or receive provider credentials.

## Prepare an export

1. Install the publication dependencies:

```sh
uv sync --extra hub --extra dev
```

2. Create a new export directory:

```sh
uv run python scripts/export_huggingface.py --output build/huggingface
```

The export creates a static Space and a results Dataset.
The Space card contains the tags that the Leaderboard Finder requires.
The Dataset contains the current model exhibition.
It excludes the previous exhibition and local baseline groups.
It does not add entries to the empty official leaderboard.

Each row identifies one agent and one game.
The export retains scores, seeds, model revisions, task versions, latency and trust status.
A suite ID identifies the test conditions.
The `suite_` columns repeat campaign measurements on each game row.
Do not add these values across rows.

The root JSONL files retain nested metadata.
The viewer files store variable engine and provider metadata as JSON strings.
This format prevents conflicts between Dataset viewer column types.
The exported `snapshot.json` is identical to the Space file `data.json`.
Both files exclude the removed result groups.
The publication record also retains the source snapshot checksum.
A checksum manifest covers every export file.

## Publish an export

Use an authorized Hugging Face account with write access to both target repositories.
Supply credentials through `hf auth login` or the `HF_TOKEN` environment variable.
Do not put tokens in source files or command arguments.

1. Commit the source changes.
2. Run this command from the source repository:

```sh
uv run python scripts/publish_huggingface.py \
  --export build/huggingface \
  --source-commit "$(git rev-parse HEAD)" \
  --receipt build/huggingface-receipt.json
```

The publisher first verifies the file inventory and checksums.
It then publishes the Dataset and records its commit ID.
The Space update contains a link to that exact Dataset commit.
The Space file `publication.json` records the source commit and the snapshot checksum.
The local receipt also records the Space commit.

The GitHub workflow **Publish Hugging Face leaderboard** supports manual publication.
It requires the repository secret `HF_TOKEN`.
Use a token with write access to the two GeneralGameBench repositories.
The workflow does not run on a schedule.
A local publication does not configure this secret automatically.

## Verify publication

1. Confirm that the Space has the `RUNNING` state.
2. Open the Space and select each result group.
3. Open each Dataset configuration in the Dataset viewer.
4. Compare the Space snapshot checksum with the Dataset snapshot checksum.
5. Keep the publication receipt with the release records.

The tests load the viewer files with the Hugging Face Dataset library.
They compare every exported score with its source value.
They also verify the Finder tags and the fixed Dataset revision link.
A changed export must fail checksum verification before publication.

## Leaderboard Finder

The Finder requires a public Space and the `leaderboard` tag.
GeneralGameBench uses these classification tags:

| Tag | Meaning |
| --- | --- |
| `domain:gaming` | Proposed Gaming category |
| `modality:image` | The agent receives game images. |
| `modality:agent` | The agent sends control actions. |
| `eval:performance` | The test measures response time. |
| `submission:semiautomatic` | Contributors run tests and submit evidence for review. |
| `test:public` | Test definitions and seed values are public. |
| `judge:function` | Game rules calculate the scores. |
| `language:english` | Instructions and control descriptions use English. |

The current Finder does not define a Gaming category.
The proposed change adds this category to its sections, filters and submission guide.
The category appears when the Finder contains an approved entry with `domain:gaming`.
The change does not bypass maintainer approval or change the index data.

The Finder requires at least five community likes on the Space.
Its maintainers control approval and the category change.
Publication of the Space does not confirm inclusion in the Finder.

Sources: [Leaderboard guide](https://huggingface.co/docs/leaderboards/en/leaderboards/building_page),
[Finder submission rules](https://huggingface.co/spaces/OpenEvals/find-a-leaderboard/blob/main/client/src/pages/HowToSubmitPage/HowToSubmitPage.jsx),
[Space metadata](https://huggingface.co/docs/hub/en/spaces-config-reference),
and [Dataset configurations](https://huggingface.co/docs/hub/en/datasets-data-files-configuration).
