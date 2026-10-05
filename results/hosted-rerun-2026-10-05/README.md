# Hosted model rerun on the Mac

This campaign reruns the eleven hosted models that completed the earlier campaign.
It keeps each requested OpenAI and Anthropic model ID. It does not substitute models.
The [inventory](model-inventory.json) lists the models.

Each model uses all 43 scenarios, seed 3000, evaluator 0.5.0, and a limit of eight
decisions per scenario. The prompt remains `pixels-json-action/2`.
The [declaration](campaign.json) records the fixed source checksums and settings.
SuperTuxKart uses task version 3 and renderer `deterministic-render-v2`.

The Mac runs one model and one game at a time. The providers run model inference
on their servers. Hugging Face hosts the result page and Dataset.
Each action starts a fresh authenticated command process. The timer includes
command startup, image transfer, network time, inference, and action validation.
The game waits for the action. Engine advancement is outside the timer.
Hosted weights do not have a pinned commit. Provider metadata records the
requested model ID and any resolved model ID that the provider supplies.

These calls use a different inference path from the four local MLX models.
MLX retains model weights in memory and uses three gray startup images.
Hosted calls start a new command process for each game image.
The table shows the test conditions for each model. It does not measure model-only speed.

The latency test pools all recorded response times from a complete suite.
It calculates p95 with linear interpolation. A value below 200 ms passes.
Exactly 200 ms fails. Scores, errors, and trust status remain separate.
All scored failures stay in the evidence. A reply error ends its episode and
gives it zero points. A missing suite receives no total score.

The referee checks each native replay immediately after recording.
The exporter checks the evidence again before publication. It rejects changed
source files, mixed tasks, and incomplete model suites.
The four verified local vision models remain in the table. Earlier runs remain
unchanged in the archive. These short tests check integration. They do not
establish model skill. All results remain local-unattested.

## Measured results

All eleven models completed the 43-scenario suite. The new runs contain
473 episodes and 3,721 recorded decisions. They retain all 11 reply errors:
eight invalid JSON replies and three provider call failures.
An error ends its episode and gives it zero points. No failed episode was replaced.

| Requested model | Score / 100 | Suite p95 / ms | Reply errors | Decisions |
| --- | ---: | ---: | ---: | ---: |
| `gpt-6-astra` | 18.125 | 18023.87 | 0 | 342 |
| `claude-opus-5[1m]` | 17.998 | 3273.09 | 0 | 340 |
| `gpt-5.6-terra` | 17.992 | 15372.74 | 0 | 340 |
| `claude-sonnet-5` | 17.757 | 2761.46 | 0 | 340 |
| `gpt-5.5` | 17.344 | 12131.92 | 0 | 340 |
| `gpt-6-sol` | 15.703 | 14712.85 | 3 | 336 |
| `gpt-5.6-sol` | 15.323 | 16570.74 | 0 | 344 |
| `gpt-6-luna` | 15.030 | 17991.21 | 0 | 344 |
| `gpt-5.6-luna` | 14.437 | 13674.89 | 0 | 344 |
| `claude-sonnet-5-5` | 14.176 | 4268.19 | 4 | 320 |
| `claude-haiku-4-5-20251001` | 13.201 | 15912.67 | 4 | 331 |

None of the eleven models passed the latency test. The test uses the unrounded
response times. Scores do not remove or replace the latency result.

The combined table contains 15 models, 645 episodes, and
4,208 recorded decisions. It retains all 138 reply errors.
The four local vision model rows remain unchanged. None of the fifteen models
passed the test for suite p95 below 200 ms.

## Evidence checks

All 473 new episodes passed native replay after recording. They passed native
replay again before this export. The exporter checked all 104 fixed source
checksums before and after replay. It also checked each saved result against
its event ledger and the declared game and model settings.

The 172 local model episodes keep their earlier native replay proof. Their source,
ledger, image checksums, and ranking were checked again. The
[retained evidence report](retained-evidence.json) identifies that proof.
The [validation report](validation.json) records an independent calculation of
each score, pooled p95, error count, and decision count.

The [previous snapshot](previous-snapshot.json) keeps the four-model table
without changes. Its SHA-256 is `83b8ac55725e66ed2db376b4ea651262d970b079fdd3b755dd32374b47b7775a`.
The earlier archive links and historical result groups remain unchanged.
The public page and Dataset exclude local baselines and previous-result views.

The [release files](https://github.com/DanielTea/generalgamebench/releases/tag/hosted-rerun-2026-10-05)
contain all 645 selected episode ledgers, saved results, and PNG observations.
The [source tag](https://github.com/DanielTea/generalgamebench/tree/hosted-rerun-2026-10-05-source)
and the campaign checksums identify the fixed evaluator.
The full Linux validation remains in the [Linux report](../linux-2026-10-05/README.md).
These new scored runs used the Mac. The providers ran model inference.

The Hugging Face Dataset keeps two suite identifiers. They use the same games,
seed, decision limit, prompt, and referee. One records the local MLX test
conditions. The other records the hosted command and network path.
These timings measure the complete response path. They do not measure model-only speed.
