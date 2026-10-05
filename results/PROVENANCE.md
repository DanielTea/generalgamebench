# Measured results provenance

## Current combined model results — 5 October 2026

Eleven OpenAI and Anthropic models completed new runs with the current renderer.
Each model used all 43 scenarios, seed 3000, and a limit of eight decisions.
The Mac ran one model and one game at a time. The providers ran model inference.
The new runs contain 473 episodes, 3,721 decisions, and 11 reply errors.
Every new episode passed native replay twice. All 104 fixed source checksums match.

The combined table keeps the four verified local vision model rows unchanged.
It now contains 15 models, 645 episodes, 4,208 decisions, and 138 reply errors.
No model passed the test for suite p95 below 200 ms. Exactly 200 ms fails.
Scores, errors, and trust status remain separate. All entries remain
`local-unattested`. The official leaderboard has no entries.

The [campaign report](hosted-rerun-2026-10-05/README.md) gives the model results
and evidence checks. The [previous snapshot](hosted-rerun-2026-10-05/previous-snapshot.json)
keeps the four-model table without changes. Earlier archives remain unchanged.
The public page and Dataset still exclude local baselines and previous-result views.

Each hosted action uses a fresh authenticated command call. Its measured time
includes command startup, image transfer, network time, inference, and action
validation. The local MLX path keeps weights in memory. The Dataset records
these test conditions under two suite identifiers. These timings do not measure
model-only speed. The short runs check integration. They do not establish model skill.

## Earlier Mac vision model results — 5 October 2026

The model table contains four vision models from Hugging Face. Each model ran
all 43 scenarios on the Mac with seed 3000 and a limit of eight decisions.
The campaign contains 172 episodes and 487 recorded decisions.
It retains all 127 reply errors. None of the four models passed the latency test.
The suite p95 must be below 200 ms. Exactly 200 ms fails.

The [campaign report](hf-vlm-2026-10-05/README.md) gives the measured results,
model revisions, startup procedure, source checksums, and replay evidence.
These short runs check integration. They do not establish model skill.
All entries remain `local-unattested`. The official leaderboard has no entries.

The [previous snapshot](hf-vlm-2026-10-05/previous-snapshot.json) preserves the
earlier table without changes. Its checksum is in the new snapshot.
Earlier releases and campaign directories retain their original recording rules.
The [Linux validation report](linux-2026-10-05/README.md) records successful native
checks for all 43 scenarios on Linux x86_64.

## Earlier latency policy update — 5 October 2026

The current leaderboard limit is **suite p95 below 200 ms**. Exactly 200 ms fails.
The update uses every saved response time from each complete suite.
It uses linear interpolation across all decisions. It does not average per-game p95 values.
Scores, failures, evaluator versions and trust status stay unchanged.
This policy update adds no new leaderboard episodes or model calls.

All four controls in that model exhibition pass this latency test.
Its 11 hosted models fail it.
All four policies in the separate 516-episode baseline archive also pass it.
All entries remain `local-unattested`. The official leaderboard has no entries.

| Baseline | Score / 100 | Suite p95 / ms | Below 200 ms |
| --- | ---: | ---: | --- |
| Pixel Tracker | 16.070 | 39.926 | Pass |
| Pixel React | 15.906 | 40.123 | Pass |
| Random | 13.325 | 37.573 | Pass |
| Idle | 11.727 | 39.651 | Pass |

The [policy snapshot](policy-p95-200-2026-10-05/snapshot.json) records the new status of all 44 saved rows.
The [validation report](policy-p95-200-2026-10-05/validation.json) records the input checksums and each status change.
Run `scripts/update_latency_policy.py` with the files listed in that report to reproduce the update.

The sections below describe the rules and evidence at each original publication.
Their 100 ms references are historical. Released evidence and snapshots remain unchanged.
The current [methodology](../docs/METHODOLOGY.md) gives the new rule.

---

## 5 October 2026 — complete headless baseline refresh

The four built-in policies — **Idle, Random, Pixel React and Pixel Tracker** — each played all **43 admitted scenarios**, with seeds 4000–4002 and a 24-decision horizon in realtime mode on evaluator 0.4.0. The complete cohort contains **516 episodes and 11,641 recorded decisions**. Every scheduled episode is retained, including **21 timeouts**, which abort their episodes and score zero. No hosted model or local VLM was called.

Scored episodes ran one at a time on the shared Apple M3 Max with 48 GiB RAM and 16 CPU cores. This campaign started its replay audit only after recording finished. Other desktop and project activity was uncontrolled. Each episode starts a fresh policy process with the published RNG seed (1729), matching the public CLI. Fixed readiness and codec initialization happen before the scored clock. All game rendering is off screen, including Airstriker's explicit `rgb_array` mode.

| Policy | Score / 100 | Suite p95 | Suite maximum | Timeouts |
| --- | ---: | ---: | ---: | ---: |
| Pixel Tracker | 16.070 | 39.93 ms | 182.97 ms | 7 |
| Pixel React | 15.906 | 40.12 ms | 169.89 ms | 6 |
| Random | 13.325 | 37.57 ms | 137.25 ms | 4 |
| Idle | 11.727 | 39.65 ms | 243.14 ms | 4 |

**All four fail the strict sub-100-ms gate.** A low p95 does not override a single late or failed response. Timeouts occurred in Warzone (12), OpenTTD (5), Mindustry (3) and SuperTux (1). The response clock includes screenshot retrieval, PNG encoding and communication as well as policy work, so these timings are not policy-only inference measurements. Every row remains local-unattested; the official track is empty. The three-seed intervals overlap between the two pixel policies and describe seed variation only.

The new `local` result group has a different task set and evaluator from the prior 33-scenario baseline cohort. The old rows and their original metadata remain under `local_previous` in the source snapshot. A later user request removed baseline and previous-result views from the public page and Hub export. This refresh preserves that layout. The source snapshot and GitHub archives retain the baseline data. Both model exhibition arrays, their metadata, availability records and original campaign pointer are preserved. The shorter model exhibition has different seeds, horizon and mode, so its aggregate scores are not directly comparable to these baseline scores.

### Evidence and reproduction

[The campaign declaration](baselines-2026-10-05/campaign.json) records the matrix and source hashes before recording. Its implementation commit is `a75a640`, and no scored source changed during this campaign. `episodes.json` contains all final episode records; `evidence-roots.json` binds the selected ledgers; `replay-validation.json` records exact replay checks for all 516 episodes. The exporter refuses incomplete matrices, mismatched result sidecars, changed sources or overwritten snapshots. Failed episodes were not rerun for a better outcome. After replay finished, the publication branch merged the new Hub exporter and its optional dependencies. The recorded source hashes and original implementation commit still identify the scored environment; no gameplay was regenerated.

The [baseline release](https://github.com/DanielTea/generalgamebench/releases/tag/baselines-2026-10-05) contains the full PNG observations, event ledgers and result records in `generalgamebench-evidence-baselines-2026-10-05.tar.gz` and `SHA256SUMS`. This evidence archive is a normal tar.gz, requiring no delta codec. Extract into a fresh directory, install the relevant pinned game runtimes, and replay any restored episode:

```sh
uv run generalgamebench verify /path/to/extracted/runs/baselines-2026-10-05/tracker/coin-run-4000
```

The Hub exporter keeps the current model results only, as requested in the later publication task. It excludes baseline and previous-result groups. This refresh does not republish the Hub repositories or restore their removed views. The baseline evidence remains in GitHub and the website data download. Archives contain no credentials, model weights or game-engine binaries. Game media retains its separate rights. See [the runtime guide](../environments/README.md) and [scoring methodology](../docs/METHODOLOGY.md).

---

## 5 October 2026 — hosted-model refresh

The new cohort evaluates **eleven accessible configured models across all 43 admitted scenarios**, plus four matched reference policies. Seven OpenAI models and four Claude models, including the explicitly requested Sonnet 5.5, completed the fixed suite. Opus 5.5 returned a provider-access error through the configured connection; its one attempted episode is preserved separately and receives no aggregate score. No fallback model is substituted.

The scored cohort contains **645 episodes and 4,933 recorded decisions**: 473 model episodes and 172 control episodes. All use seed 3000, an eight-decision horizon and exhibition mode on evaluator 0.4.0. It contains **52 aborted episodes**, each scored zero: 38 provider/transport failures and 14 JSON response-format failures. The separate unavailable Opus 5.5 attempt adds one failed decision. Failures were retained rather than replaced by successful retries. One explicitly approved Codex reset credit was used during the campaign; failed episodes from before the reset remain in the scores.

This is a short integration demonstration, not a reliable measure of model intelligence or general game-playing skill. One seed provides no confidence interval; many games barely start in eight decisions. Every current model and reference row fails the strict all-responses-below-100-ms gate. The official track remains empty. Hosted calls use the authenticated CLI once per image, including startup and network overhead. Up to eleven hosted evaluations temporarily overlapped on the shared Mac; these are not isolated latency measurements. See the campaign's concurrency and recovery notes.

### Scoring and historical comparison

Each task maps its native reward to [0,1] with frozen task rules. Seeds are averaged within each scenario, then all 43 scenario means receive equal weight and the result is multiplied by 100. Errors and aborted episodes disqualify timing eligibility; aborted scores are zero. The speed gate does not multiply or otherwise alter the exhibition score. Families with several scenarios receive more total weight. Normalization anchors do not represent IQ, human performance or percentage of games beaten.

The earlier 33-scenario v0.2 exhibition, including seven local vision models, is preserved as `exhibition_previous`. Its 693 episodes and the 396 original local-control episodes remain unchanged. Old and new aggregate scores must not be compared directly. Hugging Face exports retain each track's original suite and hardware metadata in separate Dataset configurations.

### Headless execution and reproducibility

The spaceship window came from Stable-Retro's default human renderer. Airstriker now explicitly uses RGB-array rendering, so both gameplay and replay run off-screen. All 15 original Airstriker episodes passed exact frame, metadata and score replay under the fixed adapter. A real-engine regression check rejects any attempt to open its display. Other admitted engines use RGB arrays, hidden windows, Unity batch mode or container-local virtual displays.

`refresh-2026-10-05/campaign.json` retains the original scored source hashes and the final replay source hashes separately. The only engine-source change during this campaign is Airstriker's display mode, made after its complete cohort was recorded; no scored episode was replaced. The original timings remain as measured. `headless-replay.json` records the exact checks, and `validation.json` records the automated tests and final audit. The source implementation before this display fix is commit `486b6f1bf9820c67434c2e1ab77783fdfc367f78`; the fix and regression tests are in `069dc88e21367aebd33433b7a840fb04425fcbff`.

`episodes.json` contains every scored episode; `incomplete-episodes.json` preserves the unavailable model attempt. `evidence-roots.json` binds the complete public selection to its ledger hashes, and `replay-validation.json` contains its exact replay checks. The [refresh release](https://github.com/DanielTea/generalgamebench/releases/tag/refresh-2026-10-05) packages the selected ledgers, results and PNG observations plus a portable Hugging Face export and SHA-256 checksums. No credentials, provider logs, model weights or game executables are included. Nothing has been uploaded to Hugging Face.

---

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
