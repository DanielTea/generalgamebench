# Jev with native images

The Jev adapter receives the original PNG frame.
TypeSafe requires both image dimensions to be at least 280 pixels.
For smaller frames, the adapter repeats pixels with integer nearest-neighbor upscaling.
It keeps the full image and aspect ratio. It adds no new scene information.
Frames that already fit are sent without changes.
This preparation time remains inside the response clock.
It sends no game coordinates, rewards, seeds, OCR or generated image descriptions.
The frozen exhibition prompt supplies the game rules and controls.
A native Choice question lists the same allowed integer actions.
The adapter returns the selected integer to the referee.

Image requests use the `TypeSafe-Danger-Zone-Images: true` header.
TypeSafe currently calls image support experimental.
See the [image documentation](https://docs.typesafe.ai/images).

## Prepare the run

Install the [43-scenario runtimes](../environments/README.md).
Configure `TYPESAFE_API_KEY` in the process environment.
Keep the key out of source files, command arguments and evidence.
The scripts read the key from the environment and exclude it from provider metadata.

Resolve `jev-latest` with unscored gray images:

```sh
uv run python scripts/preflight_jev.py --output build/jev-preflight.json
```

Use a new report directory for each campaign.
If the Docker images were rebuilt, audit one fixed published trace per scenario:

```sh
uv run python scripts/verify_rebuilt_engines.py \
  --base-report results/hosted-rerun-2026-10-05 \
  --output results/jev-image-2026-11-05/engine-rebuilds.json
uv run python scripts/declare_jev.py \
  --preflight build/jev-preflight.json \
  --report results/jev-image-2026-11-05
```

The declaration pins the resolved model, source checksums, suite and previous snapshot.
The rebuilt images must use the same pinned engine sources and task metadata.
Only their container image IDs can differ.
The audit checks exact frames and native scores for one saved trace per scenario.
It does not establish equivalence for all possible action sequences.
Each new result retains its actual image ID.

## Record and verify

```sh
uv run python scripts/run_jev.py --report results/jev-image-2026-11-05
uv run python scripts/export_jev.py --report results/jev-image-2026-11-05
```

The model and games run serially.
Three gray startup requests precede the scored calls.
The adapter uses a persistent direct HTTPS connection.
It opens a new connection after five seconds without a request.
It does not retry model requests or substitute an action after failure.
All errors remain in the recorded results. Aborted episodes score zero.
The exporter requires all 43 episodes and checks each with native replay.
It retains all previous model rows without changes.

The response clock includes capture, encoding, transfer, inference and validation.
Game advancement occurs outside this clock.
The current leaderboard combines 70% quality and 30% speed with a geometric mean.
There is no hard latency cutoff. The original Jev campaign keeps its former latency flags as historical evidence.
The direct API path differs from the fresh command process used for earlier hosted models.
Each result identifies its transport and startup conditions.

One seed and eight decisions per scenario check integration.
These short runs cannot establish model skill.
Results remain `local-unattested` in the model exhibition.
Use the [publication procedure](HUGGING_FACE.md) after verification.
