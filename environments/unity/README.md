# Unity VisualFoodCollector

The `unity-food-collector` task uses the official ML-Agents 1.1.0 example. Linux x86_64 uses `assets-linux.json`. The Mac uses `assets.json`; Apple Silicon runs this Intel build under Rosetta. Each file pins the archive and the extracted input tree. The input digest excludes generated profiler timers.

On Linux, follow the [full-suite installation steps](../linux/README.md). The worker uses a private Xvfb display. It enables the visual camera and uses software OpenGL rendering.

Install a separate Intel Python 3.10.12 environment, then the pinned dependencies and official application:

```sh
uv python install cpython-3.10.12-macos-x86_64-none
uv venv --python cpython-3.10.12-macos-x86_64-none .game-envs/unity
uv pip install --python .game-envs/unity/bin/python -r environments/unity/requirements.lock
uv run python environments/unity/install.py
```

The `generalgamebench.unity_engine.UnityPixelsEnv` helper loads VisualFoodCollector, selects the lowest initial agent ID, passes through its native 84×84 RGB camera and gives all peers no-op actions. Private vectors, IDs, rewards and masks are never part of a participant observation. Eight discrete controls map to the native continuous movement and binary fire controls. The production runner supervises it in the separate Unity runtime.

Each decision advances to the controlled agent's next native decision or terminal observation. Capture rate is fixed at 30; this is a lockstep task. Green food gives +1 and red food gives −1. Sum native rewards and divide by ten, clamping the aggregate to [0,1] while retaining the raw score. Stop at native termination or the declared decision horizon; there is no automatic reset inside an episode. Ten net food rewards is a benchmark target, not the maximum possible native score.

The admission tests compare every PNG, score and metadata field across fresh workers, including a 178-action seed-2 trajectory that collects positive food. Additional 200-decision random-control episodes collected food on seeds 5000 and 5001 and replayed through the full referee. These tests validate this one scene and control mapping, not arbitrary Unity games. Existing v0.2 leaderboard rows do not include this new task.

```sh
GGBENCH_RUN_INTEGRATION=1 uv run pytest tests/test_integrations.py -k unity -q
uv run generalgamebench run --agent random --games unity-food-collector --seeds 2 --start-seed 5000 --steps 200 --mode exhibition --output runs/unity-example
```

The executable remains a separately downloaded third-party asset. Its source is the official Unity ML-Agents example bundle; see [integration diagnostics](../../docs/INTEGRATION_ATTEMPTS.md).
