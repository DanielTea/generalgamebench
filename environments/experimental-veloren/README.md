# Veloren diagnostic — not admitted

Pinned official source `f6294887b13b287160d2de75809675ee521f65f4` (0.18.0) builds with `nightly-2026-06-13` and runs its native Vulkan renderer under Linux ARM64 Docker on this Mac. The original single-player world, normal character creation, native movement/interaction input and native screenshot path work.

The published prototype synchronizes the local server with frontend ticks, fixes the simulation step to 1/30 second, waits for 200 session frames, then accepts one decision per three frames. The private counter observes native item-collection events. It does not create items, move the character directly or change the inventory. The camera is the complete 960×640 native screenshot using the game's minimal graphics preset.

**It is not a validated benchmark task.** Two independent runs of the ten controls in `diagnostic.json`, one with added input delays, returned 11 frames each; all 11 differed. The initial images differed at 14,444 of 614,400 pixels. Asynchronous terrain preparation, startup timing and remaining engine randomness still need investigation. No rewarded collection route has been established. The registry and standings exclude this candidate.

## Reproduce the diagnostic

Clone the official repository at the exact revision in `diagnostic.json` into `.game-cache/veloren-source`, fetch/check out its Git LFS assets, and verify the patch checksum. Apply `lockstep-prototype.patch`, copy this Dockerfile into the source root, and build there:

```sh
docker build -t ggbench-veloren:diagnostic .game-cache/veloren-source
mkdir -p .game-cache/veloren-diagnostic
docker run --rm --init --network none --entrypoint python \
  -e TAG=first -e 'ACTIONS=[0,0,1,1,1,1,1,6,0,0]' \
  -v "$PWD/.game-cache/veloren-diagnostic:/out" \
  -v "$PWD/environments/experimental-veloren/probe.py:/probe.py:ro" \
  ggbench-veloren:diagnostic -u /probe.py
```

Repeat with `TAG=replay` and `DELAY=0.1`. The controls are wait (0), forward/right/back/left (1–4), jump (5), interact (6), camera pan left/right (7–8). Native world content currently uses the upstream default world seed; the prototype's `GGBENCH_SEED=71` only seeds one dynamic-content generator. This is not complete seed control.

Before admission: deterministic startup, complete native randomness and asynchronous mesh synchronization, a verified task objective and negative controls, robust terminal handling, then exact delayed replay through the packaged referee. Keep this development image separate from admitted game workers. Do not submit diagnostic runs as rankings.

Veloren and the derivative source patch retain the upstream GPL-3.0 license in [LICENSE](LICENSE). Assets retain their upstream notices. The repository does not include the game binary or LFS asset files.
