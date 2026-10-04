# SuperTuxKart Lighthouse

`supertuxkart-lighthouse` task version 2 runs PySuperTuxKart2 0.7.4 with the explicit `deterministic-render-v1` patch, official SuperTuxKart 1.5 assets and Mesa software rendering in Linux ARM64. It was validated through Docker Desktop on an Apple Silicon Mac. The unpatched Mac renderer remains unadmitted because repeated runs produce different animation pixels.

```sh
uv run python environments/docker-stk/install.py
GGBENCH_RUN_INTEGRATION=1 uv run pytest tests/test_integrations.py -k supertuxkart -q
uv run generalgamebench run --agent random --games supertuxkart-lighthouse --seeds 2 --start-seed 5000 --steps 200 --mode exhibition --output runs/stk-example
```

The installer verifies the upstream source revision, pybind11 submodule, patch checksum, downloaded asset archive and extracted asset tree. The release does not contain engine binaries or game assets. Preserve the built image for a cohort: every episode records its immutable image ID, engine revision, patch variant and asset digest, and replay rejects a different image. Pinned source and Python packages do not make changing distribution system packages bit-for-bit reproducible.

The native camera is 320×240 RGB. Six controls are exposed: wait, accelerate, accelerate-left, accelerate-right, brake and rescue. Each decision advances 0.2 simulated seconds. One player-controlled kart drives one Lighthouse lap, without opponents. Initialization waits for the native race start and then advances 50 fixed neutral decisions to settle the introduction. The seed and private kart/track state stay with the referee.

Score is the current nonnegative native overall distance divided by native track length, clamped to [0,1]; raw progress, distance, track length and native finish status remain in evidence. In particular, the negative pre-start sentinel must never award a lap. Native race completion or the declared horizon ends an episode. The progress regression covers 200 actions and compares all 201 camera frames, scores and metadata across fresh containers with deliberately different delays between actions. Separate wait/rescue checks cover false progress at the starting line. This validates one time-trial task, not the entire game.

## Explicit engine variant

The patch stops the Irrlicht wall clock and advances it from physics ticks, including the material wind timer. It also preserves scene registration order instead of sorting solid objects by texture pointer addresses. That removes process-dependent depth ties found in the broader seed-5001 random-control trace. It does not mask or discard image regions. The task uses the complete native rendered image; exact PNG equality remains the admission gate. The patch also allows explicit native ARM compilation on macOS for diagnostics, but only the Linux ARM64 renderer is admitted. The frozen v0.2 standings do not include this new task.

The trusted game container has no external network, drops capabilities, uses a read-only filesystem and mounts only referee source and verified game assets. The participant runs separately. This is dependency isolation for local evaluation, not independent hostile-agent attestation.

The upstream engine and this derivative patch are GPL-3.0-or-later, with bundled components and assets retaining their separate notices. See [COPYING](COPYING) and [upstream source](https://github.com/bpiwowar/pystk2/tree/dd70f6823f248ae1df2ce513839a9b2c8c940c39). The benchmark's original-code MIT license does not override these terms.
