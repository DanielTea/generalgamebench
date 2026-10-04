# GeneralGameBench

[![The GeneralGameBench environment catalog: runnable games and research candidates](site/dist/media/environment-atlas.png)](https://danieltremer.com/generalgamebench/#games)

*45 environment cards: 3 runnable cards covering 10 scenarios, plus 42 research candidates. [Image credits](docs/MEDIA.md).*

> Other benchmarks test productivity/usefulness, we test intelligence.

[Leaderboard](https://danieltremer.com/generalgamebench/) · [Project board](https://github.com/users/DanielTea/projects/4) · [Measured evidence](results/PROVENANCE.md)

Open-source, pixels-only game-agent evaluation. Render a game, issue a fresh observation, validate an action, measure the complete response path, and record referee-owned evidence.

**Early reference implementation.** Two original 2D games and eight ViZDoom 3D scenarios run today. Commercial titles are researched integration candidates, not supported games. The motto describes our ambition; this benchmark measures bounded visual gameplay, not intelligence in its entirety.

Formerly ScreenQuest Arena. The package and Python module are now `generalgamebench`; the `arena` command remains available as a compatibility alias. Published Season 0 evidence remains unchanged.

## Try it

```sh
uv sync --extra doom --extra dev
uv run generalgamebench games
uv run generalgamebench run --agent react --games coin-run dodge-lanes doom-basic --seeds 10 --output runs/react
uv run generalgamebench rank runs/react --games coin-run dodge-lanes doom-basic --seeds 10 --output results/local.json
```

macOS or Linux, Python 3.11+; Python 3.12 tested. Native Windows transport is not supported; WSL2 is an untested option. Omit `--extra doom` for the two bundled games. No game accounts or API keys required for the baselines. `uv.lock` pins the evaluation environment.

## Bring your agent

Read one JSON line with an image and allowed controls. Reply with the observation's nonce and one integer action. Start by printing `{"ready":true}`. There are no game coordinates, rewards or seeds in the observation. See [the runnable example](examples/agent.py) and [protocol](docs/PROTOCOL.md).

```sh
uv run generalgamebench run --agent-command 'python examples/agent.py' --name my-agent --output runs/my-agent
```

Run only your own trusted agents on your workstation. A subprocess is a protocol boundary, **not a security sandbox**. Submission review never executes arbitrary code in pull-request CI.

## Ranking rules

- **100 ms means strictly less than 100 ms for every measured decision**, including rendering, encoding, transport, inference, parsing and validation. Exactly 100 ms fails. p50, p95, maximum and misses are published.
- Realtime mode has a 100 ms response deadline and applies wait for late responses. A timeout aborts the episode with score zero. Simulation is currently lockstep; these results do not prove continuous real-time commercial-game control.
- Exhibition mode allows slow decisions. Astra and Claude may be compared here without being represented as sub-100 ms agents.
- Use identical game versions, horizons, seeds, hardware and observation/control interfaces. Scores are normalized using fixed scenario-specific ranges and averaged equally across the fixed game suite. No invented Elo for independent single-player episodes.
- Local scores are **provisional, unattested**. The official leaderboard stays empty until an independently administered isolated runner and attestation service are deployed. A hash chain detects modifications against retained evidence; it does not prevent a local operator rewriting a whole run.
- Confidence intervals resample seed blocks. Small exhibition samples are demonstrations, not reliable model rankings.

See [methodology](docs/METHODOLOGY.md), [security](SECURITY.md), [research](docs/RESEARCH.md), and [game catalog](docs/GAMES.md).

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
