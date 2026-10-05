# Mindustry: Ground Zero copper

For Linux x86_64, use the [full-suite installer](../linux/README.md). The installer selects an AMD64 image on that platform. Apple Silicon uses the existing ARM64 image.

This adapter runs the official Mindustry v160.5 desktop game and its built-in
Ground Zero map. The introductory task is to mine 15 copper using ordinary
movement and mouse controls. It does not claim campaign-wide coverage.

```sh
uv run python environments/docker-mindustry/install.py
GGBENCH_RUN_INTEGRATION=1 uv run pytest -q tests/test_integrations.py -k mindustry
```

The installer verifies the SHA-256 of every downloaded artifact and compiles
Arc's ARM64 SDL native library from its pinned source. Docker Desktop supplies
the Linux ARM64 runtime on this Mac. Xvfb and Mesa render the real game at
960 × 640. Agents receive the complete game framebuffer; copper totals are
read only by the referee.

Each decision advances six native frames at 1/60 second per frame. The pointer
starts at the center and moves 32 pixels per action. Optional effects and screen
shake are disabled. A fresh game directory and seeded random generator are
created for each episode. The engine container has no external network access.
The native clock patch prevents model response time from changing simulation
speed. This is a turn-stepped test; sub-100 ms eligibility measures agent
latency separately and does not imply native real-time competitive play.

The admission suite verified ordinary input, a 43-decision successful mining
route, and identical frames, rewards, terminal state, and runtime metadata in
independent workers, including deliberate action delays. A longer 120-decision
movement replay was also checked during development.

Mindustry is GPL-3.0; Arc is MIT. See COPYING and ARC-LICENSE. This integration
is local and unattested; container isolation is not an official anti-cheat
attestation or a sandbox for arbitrary hostile agents.
