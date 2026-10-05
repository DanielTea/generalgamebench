# OpenTTD: build the first road

For Linux x86_64, use the [full-suite installer](../linux/README.md). The installer selects an AMD64 image on that platform. Apple Silicon uses the existing ARM64 image.

`openttd-first-road` starts a new native OpenTTD 15.3 company on a seeded 64×64 map in 1950. The full 800×600 software framebuffer includes the ordinary toolbar, terrain, finances and cursor. The objective is introductory construction: native company ownership of at least two road bits scores one and ends the task. It does not measure a profitable transport network or full-game skill.

```sh
uv run python environments/docker-openttd/install.py
GGBENCH_RUN_INTEGRATION=1 uv run pytest tests/test_integrations.py -k openttd -q
uv run generalgamebench run --agent random --games openttd-first-road --seeds 2 --start-seed 5000 --steps 200 --mode exhibition --output runs/openttd-example
```

Ten controls provide wait, cursor movement in four directions, left-button press/release, the native road-toolbar shortcut, native autoroad shortcut and cancel. The cursor starts at screen center and moves 32 pixels per directional action. Press remains held while moving until release, allowing ordinary native drag construction. The referee never builds a road through an internal construction command on the agent's behalf. One decision advances a native game tick and 30 ms of UI time, after a fixed 16-tick initialization.

The explicit source patch adds a rendered framebuffer mode to the null video driver, reports it as a GUI so the ordinary new-company initialization runs, and drives native window/game real-time timers from fixed ticks. Only company-owned infrastructure is read privately for reward. The agent receives the native image and controls, without map arrays, private ownership counts or seed. Goal and random-control admission tests compare every image, reward and metadata field across fresh processes with varied response delays.

The installer pins and verifies the source revision and patch, and checks every OpenGFX 7.1 gameplay asset against `assets-hashes.json`. The trusted Linux ARM64 engine runs through Docker Desktop on this Mac with no external network, a read-only root and a temporary home/configuration. Evidence records its immutable image ID; preserve that image for replay. Local execution remains unattested. Binaries and game graphics are not included in evidence or Hugging Face exports.

OpenTTD and its source patch retain [their upstream GPL terms](COPYING.md). OpenGFX retains [its notices and license](OPENGFX-COPYRIGHT). The benchmark's MIT license does not relicense either work.
