# Cataclysm: Dark Days Ahead — first weapon

For Linux x86_64, use the [full-suite installer](../linux/README.md). The installer selects an AMD64 image on that platform. Apple Silicon uses the existing ARM64 image.

`cdda-first-weapon` starts the official 0.I-1 tutorial as its preset character and asks the player to find and wield the baseball bat. It renders the complete native 960×640 SDL tile view with UltimateCataclysm artwork, messages, menus and tutorial popups. Compass keys move or open doors. Dismiss advances a popup; wield and numbered choices use the native item menu. The first wielded bat scores one and ends this bounded task. Death or the horizon ends an unsuccessful attempt. This introductory navigation and inventory task does not measure full survival gameplay.

```sh
uv run python environments/docker-cdda/install.py
GGBENCH_RUN_INTEGRATION=1 uv run pytest tests/test_integrations.py -k cdda -q
```

The published source patch launches the native tutorial through its standard world generator, captures the complete SDL framebuffer at native key requests, and reads only readiness, wielded-item identity and death for the private referee. It does not move the player, pick up items or dismiss lessons. The player receives rendered pixels and legal control names. The native turn-based game waits for each agent key; optional animations are disabled in a fresh configuration. No camera region is masked or replaced.

A 49-decision route reaches and wields the bat. Both final worker admission tests pass exact image, score, termination and metadata replay, including deliberately delayed inputs.

The installer checks the exact source commit and patch digest and builds Linux ARM64 for Docker Desktop. The engine runs with no external network, a read-only root and a temporary user directory. Evidence records the immutable image ID. Rebuilding distribution dependencies can produce a different image; retain the image used for a cohort. Execution is local and unattested.

The game, source patch and bundled assets retain the [upstream license and attribution terms](LICENSE.txt), including the CC BY-SA terms for game content. The benchmark's MIT license does not relicense them. No engine binary is included in benchmark evidence or Hugging Face exports.
