# 0 A.D. diagnostic — not admitted

Official Release 28 (**0.28.0**) source and assets run on this Mac in Linux ARM64 Docker with native SDL2/OpenGL rendering. A seeded Mainland map, Athenian player and normal cursor/click controls gather ten wood after 246 decisions. The private referee reads the game's `StatisticsTracker.resourcesGathered.wood`; it does not issue simulation commands or reveal entities, coordinates or resources to an agent.

The native camera is 960×640. The prototype advances five native 20 ms frames per decision after a 100-frame initialization. Explicit map biome, placement and both civilizations avoid unseeded setup choices. Published changes pin render/LOS/minimap clocks, preserve stable model submission order, and initialize the native GUI sprite coordinate-rounding flag. That uninitialized flag caused process-dependent one-pixel shifts in the civilization emblem and minimap decoration. The patch also gives solid-color sprites valid texture geometry, instead of NaN texture coordinates.

**Exact visual replay remains unresolved.** The GUI initialization fix removed the large interface differences, but two initial cameras still differed at 661 of 614,400 world pixels. Model draw order, transforms, colors, mesh coordinates/normals and static material uniforms matched in additional diagnostics. A final cleaned-build run repeated all native wood counts through the 246-decision goal, but all 247 cameras differed (28 initial world pixels in that pair). Low-material and alternate-renderer trials did not satisfy the gate. No tolerance, image masking or score-only admission is used. This candidate is absent from the task registry and standings.

## Reproduce

Download the source and asset archives in `diagnostic.json` and verify both SHA-256 hashes. Extract the source to `.game-cache/0ad-source` and data to `.game-assets/0ad-0.28.0`. Apply `lockstep-prototype.patch` from the source root with `patch -p1`. Copy this directory's Dockerfile and `dockerignore` (as `.dockerignore`) into the source root. Build there:

```sh
docker build -t ggbench-0ad:diagnostic .game-cache/0ad-source
mkdir -p .game-cache/0ad-diagnostic .game-assets/0ad-0.28.0/binaries/data/l10n
docker run --rm --init --network none --user 1000:1000 \
  -e TAG=first -e SEED=71 -e 'ACTIONS=[0,0]' \
  -v "$PWD/.game-assets/0ad-0.28.0/binaries/data:/source/binaries/data:ro" \
  -v "$PWD/.game-cache/0ad-diagnostic:/out" \
  -v "$PWD/environments/experimental-0ad/probe.py:/probe.py:ro" \
  ggbench-0ad:diagnostic /probe.py
```

The output directory must be writable by UID 1000; the engine deliberately refuses to run as root. Repeat with `TAG=replay` and `DELAY=0.1`, then compare the JSON image hashes. Controls: wait (0), 32-pixel cursor up/right/down/left (1–4), left/right click (5–6), Escape/Enter (7–8). The pointer starts at (480,320). The known seed-71 route is `[4,4,3,3,3,5] + [2]*6 + [1]*7 + [6] + [0]*300`, expressed as a JSON array in `ACTIONS`.

Before admission: resolve the remaining renderer differences; package a pinned final worker; verify rewarded, idle and varied-seed input traces through exact full-referee replay. The native renderer and ordinary controls must remain the observation/action boundary. The diagnostic is a trusted local development tool, not an isolated arbitrary-participant service.

The engine and derivative patch retain the upstream GPL-2.0-or-later source terms; game data and bundled libraries retain their separate upstream notices. Original probe code is MIT. The repository and future Hugging Face exports do not contain the engine binary or game asset archive.
