# Football Academy

`football-empty-goal` runs Google Research Football 2.10.2's `academy_empty_goal_close` scenario. Tested on this Mac using Docker Desktop's native Linux ARM64 runtime and Mesa software rendering. The engine source revision and base image digest are pinned; the actual built image ID is recorded in every episode and checked during replay. Rebuilding with different system packages can produce a different image ID, so preserve the image used for a cohort.

```sh
uv run python environments/docker-football/install.py
GGBENCH_RUN_INTEGRATION=1 uv run pytest tests/test_integrations.py -k football -q
uv run generalgamebench run --agent random --games football-empty-goal --seeds 2 --start-seed 5000 --steps 200 --mode exhibition --output runs/football-example
```

The agent receives the native rendered camera downsampled by the upstream pixels wrapper to 320×180, plus ten action names: wait, eight directions, and shoot. Direction and shot controls are released before each decision, making wait neutral after previous input. No player coordinates, sticky-action vectors, ball state, or reward enters its observation. The native scoring reward is retained without checkpoint shaping. A goal scores one; native score/out-of-play/possession-change termination or the decision horizon ends the episode.

The real-engine tests verify a 17-decision goal, native termination, rejected post-terminal actions, and exact frame/score/metadata replay in fresh containers. This validates one Academy task, not full matches or the whole Football library. The frozen v0.2 leaderboard's 33-task cohort does not include this task.

The engine container runs without external networking, with a read-only filesystem, temporary scratch space, and a read-only mount of the trusted worker source. It receives no model credentials or host game libraries. The participant remains a separate process; these local tests do not provide hostile-agent attestation. Python and native diagnostics stay on stderr so they cannot corrupt the referee's JSON channel.

Upstream: [Football source](https://github.com/google-research/football/tree/ba9952130898bde2879b01ff2b49d3d48d26ce81). Engine, dependencies, fonts and game assets retain their upstream licenses. This task uses the separately built engine image and does not commit its binaries.
