# Additional Mac integration attempts

These diagnostics are not leaderboard entries. The 45-card catalog distinguishes validated tasks from candidate integrations.

## SuperTuxKart

PySuperTuxKart2 0.7.4 successfully loaded its official 1.5 assets on this Mac and accepted discrete driving controls on Lighthouse. Physics rewards replayed, but rendered tree/wind pixels differed between repeated seeded processes. Upstream [wind.cpp](https://github.com/bpiwowar/pystk2/blob/master/src/graphics/wind.cpp) reads an Irrlicht timer in addition to randomness; the exposed Python configuration does not pin that timer. The strict pixel gate excludes this task. A separate scoring test caught and corrected the negative pre-start-distance sentinel, which must not count as a completed lap.

## Luanti / Craftium

The official [Craftium 0.0.1](https://github.com/mikelma/craftium/releases/tag/v0.0.1) CPython 3.12 Linux x86_64 wheel installed in Docker on this Apple Silicon Mac. The `ChopTree-v0` environment exposed a 64×64 RGB observation and eight actions, but the native Luanti executable exited with signal 11 before connecting to its Python referee. Retests with software rendering and the softpipe driver produced the same failure. No gameplay result was produced or ranked. A native build or a validated compatible renderer/runtime is still required.

Diagnostic image: `ggbench-craftium:0.0.1`, based on Python 3.12 slim Bookworm plus Mesa runtime libraries. This local diagnostic container is not a portable validated worker and is not an adversarial-agent sandbox. The catalog continues to label Luanti as unadmitted.

## Unity

The [official ML-Agents registry](https://unity-technologies.github.io/ml-agents/Unity-Environment-Registry/) points to a prebuilt Mac example bundle. Both GridWorld and VisualFoodCollector launched through ML-Agents 1.1.0 under Python 3.10.12. GridWorld also has a private goal vector, so the chosen candidate is VisualFoodCollector with only its native RGB camera. Structured vectors and action masks remain referee-only. Pin the exact executable and assets; generated profiler timer logs are excluded from the input asset digest.

VisualFoodCollector reproduced a 128-action camera sequence exactly with its final experimental control mapping, and a straight-line probe produced a native negative-food reward. A successful positive-food collection and full referee/scoring admission were not verified. The experimental helper is excluded from `TASKS`, CLI game discovery, and all leaderboard rows. No Unity result is fabricated from the probes.

## Crafter replay correction

The full evidence audit found a version-1 Crafter frame mismatch at tick 11 for seed 4001. The upstream engine balances creature populations every ten ticks using an address-hashed object set. Sorting that set by unique tile position before balancing removes this process-dependent choice. A 132-action regression now repeats exact frames and score across four fresh workers. All 33 Crafter episodes (every model and both reference cohorts) are regenerated under task version 2; the original version-1 episodes remain local diagnostic evidence and are excluded uniformly, regardless of score.
