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
