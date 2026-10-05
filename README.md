# GeneralGameBench

[![The GeneralGameBench environment catalog: runnable games and research candidates](site/dist/media/environment-atlas.png)](https://danieltremer.com/generalgamebench/#games)

*45 environment cards: 36 validated cards covering 43 scenarios, plus nine unadmitted candidates. [Image credits](docs/MEDIA.md).*

> “Intelligence is the ability to adapt to new environments.” — We test this.

[Leaderboard](https://danieltremer.com/generalgamebench/) · [Project board](https://github.com/users/DanielTea/projects/4) · [Measured evidence](results/PROVENANCE.md)

Open-source, pixels-only game-agent evaluation. Render a game, issue a fresh observation, validate an action, measure the complete response path, and record referee-owned evidence.

**Early reference implementation.** Two original 2D games, eight ViZDoom scenarios and 33 additional tasks run on the tested Mac. Version 0.3 adds ten tasks: Unity VisualFoodCollector, Football Academy, SuperTuxKart Lighthouse, Luanti ChopTree, SuperTux, Dungeon Crawl Stone Soup, OpenTTD, Mindustry, Cataclysm: DDA and Warzone 2100. Each has native scoring and exact replay checks. The nine Linux engines use local ARM64 containers. Commercial AAA titles remain integration candidates. The motto describes our ambition; this benchmark measures bounded visual gameplay, not intelligence in its entirety.

The 5 October 2026 hosted-model refresh evaluates all 43 admitted scenarios with OpenAI and Anthropic models, plus four reference policies. It uses one seed and eight decisions per scenario: an integration exhibition, not a reliable intelligence ranking. The frozen 33-scenario v0.2 results, including local VLMs, remain in the versioned result archive. See [scoring methodology](docs/METHODOLOGY.md), [campaign evidence](results/refresh-2026-10-05) and [coverage and remaining work](docs/GAMES.md).

The subsequent [local baseline refresh](results/baselines-2026-10-05) runs Idle, Random, Pixel React and Pixel Tracker across the complete 43-scenario headless suite: three seeds and 24 decisions per episode, for 516 episodes. Scored episodes run serially, followed by exact replay verification. These are coded reference policies; no hosted model calls are involved. The previous 33-scenario baselines remain in the result archive. Model scores are unchanged. The public page keeps the two views requested later: Model exhibition and Official ranked. Use the result archive or website data download to inspect the new baselines.

Formerly ScreenQuest Arena. The package and Python module are now `generalgamebench`; the `arena` command remains available as a compatibility alias. Published Season 0 evidence remains unchanged.

## Try it

With Docker running, the portable submission workflow needs no local Python:

```sh
git clone https://github.com/DanielTea/generalgamebench.git
cd generalgamebench
./ggbench
```

This runs **ten scenarios / 50 episodes**, replays every result, and creates upload-ready evidence under `runs/submission/`. Open `SUBMIT.txt` and attach the files in `uploads/` to request community review. No account keys or hosted model calls are needed for the included policy. The portable image targets Linux AMD64 and ARM64; use Docker on Linux or macOS, or Docker through WSL2 on Windows (the WSL2 host path remains untested). The full 43-task suite still requires additional runtimes.

See [run your agent, select a suite and submit](docs/SUBMISSIONS.md). Local results remain provisional; uploads do not automatically receive an official rank.

For native Python development:

```sh
uv sync --extra doom --extra dev
uv run generalgamebench games
uv run generalgamebench run --agent react --games coin-run dodge-lanes doom-basic --seeds 10 --output runs/react
uv run generalgamebench rank runs/react --games coin-run dodge-lanes doom-basic --seeds 10 --output results/local.json
```

macOS or Linux, Python 3.11+; Python 3.12 tested. Native Windows transport is not supported; WSL2 is an untested option. Omit `--extra doom` for the two bundled games. No game accounts or API keys required for the baselines. `uv.lock` pins the evaluation environment.

Install and validate optional engines using [the runtime guide](environments/README.md). The [coverage matrix](docs/GAMES.md) states exactly which family members are implemented.

## Bring your agent

Read one JSON line with an image and allowed controls. Reply with the observation's nonce and one integer action. Start by printing `{"ready":true}`. There are no game coordinates, rewards or seeds in the observation. See [the runnable example](examples/agent.py) and [protocol](docs/PROTOCOL.md).

```sh
uv run generalgamebench run --agent-command 'python examples/agent.py' --name my-agent --output runs/my-agent
```

Run only your own trusted agents on your workstation. A subprocess is a protocol boundary, **not a security sandbox**. Submission review never executes arbitrary code in pull-request CI.

## Ranking rules

The leaderboard limit is **suite p95 below 200 ms**.
Exactly 200 ms fails.
The score and the latency result are separate.

- Use every recorded response time from the complete suite, including failed episodes.
- Calculate p95 with linear interpolation. Do not average the p95 values of individual games.
- Keep the full response path in the timer: image retrieval, encoding, transport, inference, parsing and validation.
- Publish p50, p95, maximum response time, responses at or above 200 ms, errors and aborted episodes.
- Keep aborted episodes with score zero. Reject incomplete suites.
- Use the same games, seeds, versions, hardware, interfaces and decision limits for score comparisons.
- Keep local results `local-unattested`. A latency pass does not give an official rank.

The simulation waits while the agent responds.
New runs use the configured transport timeout, which defaults to 60 seconds.
A response above 200 ms stays in the evidence and can still control the game.
A transport timeout aborts the episode.
This prevents a 200 ms response cutoff from removing the slow samples used to calculate p95.
These tests do not establish continuous real-time control.

The current board applies this rule to the saved response times.
Scores and original evidence stay unchanged.
Earlier realtime recordings used a 100 ms response deadline.
Those recordings retain their original actions, failures and evaluator versions.
Released snapshots retain the rules used at publication.
See [methodology](docs/METHODOLOGY.md), [security](SECURITY.md), [research](docs/RESEARCH.md), and [game catalog](docs/GAMES.md).

## Hugging Face

[Leaderboard Space](https://huggingface.co/spaces/danieltee/generalgamebench) ·
[Results Dataset](https://huggingface.co/datasets/danieltee/generalgamebench-results)

The Space shows the leaderboard and links to a fixed Dataset revision.
The Dataset retains scores, seeds, test conditions, latency and trust status.
Separate computers run the games.

```sh
uv sync --extra hub --extra dev
uv run python scripts/export_huggingface.py --output build/huggingface
```

This command prepares local files.
See the [publication procedure](docs/HUGGING_FACE.md) to publish them.
The proposed Gaming category uses `domain:gaming`.
Finder inclusion requires five community likes and maintainer approval.

## Structure

```text
src/generalgamebench/  referee, game adapters, protocol, evidence, statistics, policies
examples/              minimal participant and container setup
scripts/               benchmark campaigns and public-data export
results/               measured public snapshots and provenance
site/dist/             static leaderboard and downloadable data
tests/                functional, protocol, timing and evidence tests
docs/                 methodology, research, game feasibility, roadmap
```

## Development

```sh
uv sync --extra doom --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Inspired by [ScreenQuest](https://github.com/DanielTea/screenquest): separate fast control, slow reasoning, validated inputs and independent outcome evidence. This project is a new portable implementation; it does not publish local profiles, game sessions or calibration files from ScreenQuest.

MIT for original code. Third-party games, engines, models and assets keep their own licenses. See [notices](docs/THIRD_PARTY_NOTICES.md).
