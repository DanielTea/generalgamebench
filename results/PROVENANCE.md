# Measured results provenance

## Version 0.3 — native integration validation

Evaluated on 2026-10-04 on the same Apple M3 Max Mac. Ten additional bounded tasks bring the runnable catalog to **43 scenarios across 36 cards**. The new tasks are Unity VisualFoodCollector, Football Academy, SuperTuxKart Lighthouse, Luanti ChopTree, SuperTux, Dungeon Crawl Stone Soup, OpenTTD, Mindustry, Cataclysm: DDA and Warzone 2100. Nine engines run in local Linux ARM64 containers; Unity uses the pinned native Mac example.

The complete fixed integration-control cohort contains **21 episodes and 4,303 recorded decisions**, with **zero errors or aborted episodes**. Every episode passed independent exact camera, score and termination replay. Each of the ten tasks used the random reference policy with seeds 5000 and 5001 and a 200-decision horizon. A Unity idle control used seed 71 and a 1,200-decision horizon, reaching the engine's natural termination at decision 1,000. Native termination can shorten an episode.

This is validation evidence, not an expanded model ranking. **No hosted or local model was called for this cohort.** The local, exhibition and official ranking arrays remain byte-for-byte equivalent under canonical JSON hashing to v0.2. The 17-model exhibition still compares the original 33 scenarios. No new tasks are blended into those scores. All evidence remains local-unattested; the official track is empty.

`integrations-0.3/campaign.json` fixes the complete cohort and hashes every benchmark source, dependency lock and admitted runtime build file before execution. The recorder checks those hashes again after the final replay. `episodes.json`, `evidence-roots.json` and `replay-validation.json` retain every final episode, chain head and replay result. `admission-validation.json` also records the individual native checks, the 63-passing-check unit suite, and the earlier SuperTuxKart worker timeout followed by its passing isolated regression. Earlier diagnostic cohorts exposed renderer bugs and were retained locally; the entire fixed final cohort was rerun after the fixes, without score-based selection.

The [v0.3.0 release](https://github.com/DanielTea/generalgamebench/releases/tag/v0.3.0) includes the selected event ledgers, results and native PNG observations in `generalgamebench-evidence-v0.3.0.delta.tar.gz`. This compact transport restores every original file byte-for-byte. Verify `SHA256SUMS` and follow the [lossless restoration instructions](../environments/evidence-codec/README.md); then install the pinned game runtime and replay any restored episode, for example:

```sh
uv run generalgamebench verify build/restored/evidence/runs/integration-release-0.3-verified/random/warzone-first-derrick-5000
```

The separate diagnostic-media archive contains only the native preview frames for **unadmitted** 0 A.D., StarCraft II and Veloren prototypes. `diagnostic-media.json` hashes those frames; `diagnostic-replay.json` preserves the failed paired image hashes and native counters. These files do not enter scored evidence or rankings. The prototypes' precise failures and reproducible source are documented under `environments/experimental-*`. Six other game families still need usable installations/assets and adapter work.

The portable Hugging Face export contains the updated catalog and the unchanged v0.2 ranking rows. No Space or Dataset was uploaded. No archive contains engine binaries, commercial game packages, model weights or credentials. Source patches and rendered game media retain the third-party terms documented in the repository.

---

## Season 0.2 — expanded Mac suite

Evaluated on 2026-10-04. **1,089 actual episodes and 14,394 recorded decisions**, all replay-verified before publication. The suite covers 33 scenarios across 26 of 45 environment cards. At that release, nineteen cards remained unadmitted; no modern commercial AAA title is ranked. Every result is **local-unattested**, and the official track is empty.

- Local controls: four built-in policies, 33 scenarios, seeds 4000–4002, 24-decision horizon: 396 episodes.
- Model exhibition: all 17 configured vision-capable models (seven OpenAI, three Anthropic and seven fully cached local MLX models), the same 33 scenarios, seed 3000, eight-decision horizon: 561 episodes.
- Matched exhibition controls: the four built-in policies, the same seed and horizon: 132 episodes.
- There were 44 recorded errors and 44 aborted episodes. Aborted episodes score zero; they are retained, not replaced by successful retries. FastVLM's responses often failed the required JSON action protocol. These rows describe performance with this interface, not an inability to see images.

### What was measured

This is a short integration exhibition. Eight decisions barely start many games; the model cohort has one seed and no confidence interval. Hosted models use fresh authenticated CLI calls per observation; startup and network overhead are inside the response clock. Local models remain loaded, with model initialization outside that clock. Calls ran concurrently on a shared Apple M3 Max with 48 GiB RAM and 16 CPU cores (up to ten hosted evaluations and one local VLM). Latencies are observed end-to-end response times, not provider inference benchmarks or isolated hardware measurements.

The clock includes snapshot retrieval, PNG encoding, transport, inference, parsing and action validation. Engine advancement and eager rendering between decisions are outside it. All simulation is lockstep. Strictly less than 100 ms on **every** measured decision is required for latency eligibility; errors or aborted episodes also disqualify a row. Passing this local timing gate does not grant official rank.

Task definitions, score anchors and runtime installation instructions are in [environments/README.md](../environments/README.md). Families with multiple modes are admitted only for the specific tasks listed. The four built-in policies are coded references, not trained general game-playing models. The existing 2D heuristics do not confer skill in newly added games.

### Source and evidence

The original scored implementation is commit `6f6f76ca55cf9160cfe57a9eb13f2120e2e422c3`. A full replay audit found address-dependent creature selection in Crafter. Commit `ad38b2362575b537cce6638ea020b9bbb99c5e6c` fixes that ordering and records Crafter task version 2. Every Crafter episode was regenerated under that revision; the other 32 tasks and model interface are unchanged and their original episodes are retained. The campaign records both source-hash sets and the complete task-revision selection. Subsequent publication work adds UI, exports, documentation and an unadmitted Unity helper. The complete 83-check validation passed, including 26 optional real-engine checks. The report includes test-source and dependency-lock hashes.

`season-0.2/snapshot.json` is the public leaderboard; `episodes.json` retains individual scores and timing arrays; `evidence-roots.json` lists the exact included paths and final hash-chain heads. `campaign.json` records fixed source hashes, seeds, horizon and model-to-directory assignments. `model-inventory.json` and `model-status.json` preserve model IDs, local weight revisions and completion status without private paths or account configuration. `validation.json` records the actual validation checks.

Runs were split into disjoint model assignments before the secondary jobs started. Empty administrative reservations in the original driver prevent duplicate evaluations; they are not provider failures and are not included as episodes. Development connectivity probes, pre-admission engine diagnostics and earlier prompt experiments are excluded. No final run was selected by score. Each assigned model's complete final suite is included once. The whole Crafter cohort was replaced to fix the engine defect, not to improve selected scores; all original Crafter version-1 episodes remain local and are excluded uniformly.

The [v0.2.0 release](https://github.com/DanielTea/generalgamebench/releases/tag/v0.2.0) contains `generalgamebench-evidence-v0.2.0.tar.gz`, the portable Hugging Face export, and `SHA256SUMS`. Extract the evidence into a new directory, install the pinned optional runtimes, and verify an episode:

```sh
uv run generalgamebench verify /path/to/extracted/runs/expanded-models-20261004/openai-gpt-6-astra/coin-run-3000
```

The archive contains only the selected event ledgers, result records and PNG observations. It does not contain credentials, model weights, game binaries, administrative reservations or development probes. Hashes and deterministic replay make the snapshot inspectable, but they are not independent attestation of its original wall-clock timing.

### Future Hugging Face publication

The prepared static Space and separate tabular Dataset use this same snapshot. Each dataset row retains track, task/engine metadata, model revision, exact seed set, decision horizon, suite identity, latency, errors and trust. The snapshot checksum binds every exported row to the source data. Game execution and credentials stay outside the Space. Nothing has been uploaded to Hugging Face yet; see [the publication design](../docs/HUGGING_FACE.md).

---

## Archived Season 0

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
