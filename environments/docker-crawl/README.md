# Dungeon Crawl Stone Soup: first experience

`dcss-first-experience` starts a new native Dungeon:1 game as a Minotaur Fighter with a war axe. It uses DCSS 0.34.0's complete 800×600 SDL tile view, including its ordinary inventory and messages. Compass controls move or attack an adjacent enemy; wait, confirm and cancel are also available. The first native experience gain scores one and ends this bounded task. Death or the declared horizon ends it without success. This is an introductory combat objective, not a full dungeon completion score.

```sh
uv run python environments/docker-crawl/install.py
GGBENCH_RUN_INTEGRATION=1 uv run pytest tests/test_integrations.py -k 'crawl or dcss' -q
uv run generalgamebench run --agent random --games dcss-first-experience --seeds 2 --start-seed 5000 --steps 200 --mode exhibition --output runs/crawl-example
```

The pinned source patch connects native key requests to the private referee and captures the full OpenGL framebuffer before swapping. It advances the UI clock by 100 ms per key, disables optional native real-time animations in the fresh configuration, and seeds decorative wall/floor tiles from the game seed instead of the character's wall-clock creation time. The startup seed message is suppressed in the native game. No camera region is removed or replaced. The title and seed-confirmation menus are advanced before the first observation; gameplay receives no automatic exploration, fighting or prompt responses.

The referee reads native experience and health privately. The agent receives pixels and legal control names only. Seed zero, which upstream reserves for unseeded games, maps to uint64 maximum; other seeds are passed unchanged. Admission tests cover a 24-key first-experience route at seed 71, a zero-seed wait trajectory, and exact fresh-process image/reward/metadata replay with varied response delays.

The installer verifies the source revision and patch digest, then builds Linux ARM64 for Docker Desktop on this Mac. The trusted engine container runs with no external network, a read-only root and a temporary home/save directory. Evidence records its immutable image ID. Rebuilding distribution dependencies can change that ID; preserve the image used for an evidence cohort. Local execution is unattested.

The engine and this source patch retain [GPL-2.0-or-later terms and bundled notices](LICENSE). The game's tile artwork retains [its upstream notices](TILES-LICENSE.txt); the benchmark's MIT license does not relicense it. No game binary is included in evidence or Hugging Face exports.
