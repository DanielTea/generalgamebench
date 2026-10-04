# Optional game runtimes

The referee uses Python 3.12. Engines run in separate trusted worker processes because their Python and NumPy requirements conflict. This process boundary isolates dependencies, not malicious agents. `.game-envs`, weights, assets and local credentials are never committed.

On the tested Apple Silicon Mac:

```sh
uv sync --extra doom --extra dev
uv venv --python 3.12 .game-envs/research
uv pip sync --python .game-envs/research/bin/python environments/research/requirements.lock
uv venv --python 3.12 .game-envs/roguelike
DEVELOPER_DIR=/Library/Developer/CommandLineTools CMAKE_ARGS=-DCMAKE_OSX_ARCHITECTURES=arm64 ARCHFLAGS='-arch arm64' \
  uv pip sync --python .game-envs/roguelike/bin/python environments/roguelike/requirements.lock
```

NLE needs CMake, a C/C++ compiler and command-line build tools. Use an already licensed toolchain; this project does not accept platform license agreements automatically. MiniHack requires the pinned setuptools version for its legacy resource loader.

Procgen's published macOS wheel is Intel-only. The tested installation used the existing Intel Python 3.10.17 under Rosetta:

```sh
uv venv --python /usr/local/bin/python3.10 .game-envs/procgen
uv pip sync --python .game-envs/procgen/bin/python environments/procgen/requirements.lock
```

On another platform choose a compatible Python 3.10 interpreter; do not use the Mac path. The lock files record the tested environments, not a promise that every package has a wheel for every OS. Native Windows referee pipes are currently unsupported. Set `GGBENCH_ENV_ROOT` to relocate the runtime directories.

Optional local vision models use a separate Apple Silicon runtime:

```sh
uv venv --python 3.12 .game-envs/vlm
uv pip sync --python .game-envs/vlm/bin/python environments/vlm/requirements.lock
uv run generalgamebench models > runs/models.json
```

Discovery reads the configured image-capable Codex model list, Claude CLI initialization model list, and complete local MLX snapshots. It never publishes account details or downloads model weights. The discovery file contains local paths and belongs under ignored `runs/`. Models listed by a provider may still fail when called; campaign status records actual availability. FastVLM's cached processor needs torch, torchvision and timm even though model inference uses MLX. Model licenses remain separate.

## Admission and verification

```sh
GGBENCH_RUN_INTEGRATION=1 uv run pytest tests/test_integrations.py -q
uv run generalgamebench games
uv run generalgamebench run --agent random --games procgen-maze minihack-room crafter --seeds 2 --steps 24 --output runs/optional-example
```

Each admitted optional task is tested in two independent processes with the same seed and actions. Every rendered PNG, final raw reward, normalized score and engine metadata must match exactly. Tests also exercise MiniHack goal completion and Procgen automatic reset boundaries. A test of one family member is not validation of its whole library.

The registry currently admits 23 optional tasks: all 16 Procgen games, Crafter, MiniWorld OneRoom, five-piston Pistonball, ALE Breakout, the bundled Airstriker demo, NetHack Score and MiniHack Room. Combined with the two originals and eight Doom scenarios, that is 33 scenarios across 26 catalog cards. The catalog has 45 cards; 19 remain unadmitted.

SuperTuxKart Lighthouse is experimental. PySuperTuxKart2 0.7.4 runs on this Mac and uses separately cached 1.5 assets, but exact screenshot replay fails. Its wind renderer reads a render timer as well as randomness, so the task is outside `TASKS`, the CLI and published suites. Crossing the start line must not award a lap: the adapter clamps the engine's negative pre-start distance instead of subtracting it. Experimental code is not a passing integration.

## Frozen task definitions

Every task exposes rendered RGB pixels, a documented discrete action set and one referee-owned reward. Public action zero always means wait/noop; MiniWorld uses its ineffective pickup action as wait. Rewards, achievements, seed and structured game state never enter model observations.

- **Procgen:** easy mode, one level per seed, single engine thread. The first auto-reset signal ends the episode before a new level is exposed. Task-v1 reward ranges are frozen in `registry.py`; retain raw rewards. These short tasks are not official full-length Procgen scores.
- **Crafter:** unique unlocked achievements divided by 22. This is explicitly different from the published geometric-mean achievement metric.
- **MiniWorld:** OneRoom navigation reward, native termination or decision horizon.
- **Pistonball:** five pistons; the agent controls the middle piston through its local RGB view. Other pistons follow a fixed periodic policy. This is a focal-agent task, not a general multi-agent tournament. Sum that piston's reward and normalize with the fixed [-100,100] range.
- **ALE:** Breakout, four emulator frames per action, sticky-action probability zero. Raw score / 864. ALE's separately installed package supplies the ROM; this repository does not redistribute it.
- **Stable-Retro:** Airstriker Genesis demo only. One emulator step per action, buttons exposed separately, raw score / 10000. No retail ROM collection is included.
- **NetHack:** native tile renderer, score reward / 1000, fixed core and display seeds, compass/vertical/wait/more controls. This restricted-control task does not claim the full NetHack action space.
- **MiniHack:** Room-5x5, fixed core and display seeds, the same native tile renderer; reaching the goal yields one.

Clamping to [0,1] is only for aggregation; the evidence retains raw values and score metadata. Game families have different natural timescales. Equal decision budgets are a transparent integration demonstration, not proof of equal difficulty or equal simulated time.

## Timing and security

The response clock starts at the referee's observation request and ends after validating one returned action. Snapshot retrieval, PNG encoding, transport, inference and parsing are included. Engine advancement and any eager rendering performed between decisions are outside that clock. These are lockstep tasks, not continuous real-time game-control measurements. MLX model loading is before readiness; per-frame CLI startup is inside the clock. Compare these transports with that difference in view.

Pin runtime packages, assets, task version, evaluator source and hardware for comparisons. Exact replay on one machine does not guarantee cross-GPU byte identity. Local evidence remains unattested; no local result automatically enters the official track.

### Crafter task version 2

Crafter 1.8.3 keeps chunk objects in address-hashed Python sets. Its periodic creature population balancing can therefore choose different creatures despite identical seeds. The adapter sorts each chunk's objects by their unique tile positions before upstream balancing; other game mechanics are unchanged. This is an explicit benchmark variant, recorded as task version 2. The full Crafter cohort is regenerated for this task revision; version-1 episodes are not mixed into the release. The regression check repeats a 132-action seed-4001 trajectory in four fresh processes.
