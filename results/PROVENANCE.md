# Measured results provenance

Season 0, evaluated on 2026-10-04. These are actual played episodes, not sample/mock data. Trust is **local-unattested** for every result.

Hardware: Apple M3 Max, 48 GiB unified memory, macOS arm64, Python 3.12.8. This was a shared development workstation, not a dedicated calibrated evaluation host. The lockfile pins Python dependencies; `source-hashes.json` records the final reference package used for validation. No cross-hardware latency claim is made.

## Rename and reproducibility

This project was renamed from ScreenQuest Arena to GeneralGameBench in v0.1.1. Season 0 scores, evidence, source hashes, and the v0.1.0 release assets are unchanged. To reproduce the recorded source and dependency hashes exactly, check out [v0.1.0](https://github.com/DanielTea/generalgamebench/tree/v0.1.0); paths in `source-hashes.json` intentionally retain `src/screenquest_arena/`. The current package is `generalgamebench`, with `arena` retained as a command alias. The `screenquest/1` wire-protocol identifier remains stable for existing agents and recorded evidence.

## Campaigns

- `baselines-final`: four policies (`idle`, `random`, `react`, `tracker`), ten scenarios, seeds 1000–1009, horizon 80: 400 episodes. The whole campaign was rerun after nonblocking transport/deadline hardening; the earlier full 400-episode development campaign is retained locally, not mixed into the published final one.
- `exhibition-final`: `gpt-6-astra`, `claude-opus-5`, and the same four reference policies; Coin Run, Dodge Lanes and Doom Basic; seeds 2000–2001; horizon 8: 36 episodes. Eight decisions is only an integration smoke test. In particular, the Dodge Lanes horizon ends before the first falling block can collide with the player; that task provides no discrimination in this exhibition.
- Models received an actual PNG screenshot and public control instructions on each turn. Astra used Codex CLI with the explicit `gpt-6-astra` model, low reasoning, read-only mode, ephemeral state and disabled shell tool. Claude used authenticated Claude Code with image content, explicit `claude-opus-5`, low effort, disabled tools/skills/MCP and no persistence. Each image used a fresh CLI invocation; startup and network round trips are inside measured latency. No fallback model was used in the final gameplay campaign.
- The earlier Claude integration attempt failed due to incompatible streaming input/output flags, before a model action was produced. A requested Opus 5.5 configuration was not used for results; the account's working `opus` alias resolved to `claude-opus-5`, which was then explicitly pinned for the campaign. These failed setup attempts are excluded and retained locally. The successful Astra two-step connectivity test is also excluded.
- Every scheduled final episode is included. No successful gameplay run was selected by score, and failed final episodes would count as zero. The entire included evidence set passed deterministic replay before export.

## Files

`baselines.json` and `exhibition.json`: aggregates, confidence intervals, per-scenario scores and latency summaries. `episodes.json`: complete individual scores and latency arrays. `evidence-roots.json`: final SHA-256 chain heads. `source-hashes.json`: reference source/dependency hashes.

The release's `screenquest-arena-evidence-v0.1.0.tar.gz` contains the complete public campaign observations and traces. Verify the release asset SHA-256 against `SHA256SUMS`, extract to a new directory, and use the repository environment:

```sh
uv run arena verify /path/to/extracted/baselines-final/react/coin-run-1000
uv run arena rank /path/to/extracted/baselines-final \
  --games coin-run dodge-lanes doom-basic doom-defend-center doom-defend-line \
  doom-take-cover doom-health doom-corridor doom-home doom-predict \
  --seeds 10 --output results/recomputed.json
```

Hash roots published under this repository's account help detect later changes relative to this snapshot. They are not independent runner attestation. Recomputed action sequences and scores cannot prove the original wall-clock timings were produced by a trustworthy machine.

## Interpretation

The local policies are simple coded baselines, not trained general game-playing models. Pixel React and Pixel Tracker visually track the original 2D games; their Doom policies are primitive attack/movement heuristics. Eight Doom scenarios dominate the ten-scenario local suite. The model exhibition has only two seeds and a very short horizon; its ordering is a descriptive snapshot, not evidence that one model is generally more intelligent or better at games.
