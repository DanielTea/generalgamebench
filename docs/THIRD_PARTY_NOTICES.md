# Third-party notices

Original GeneralGameBench code is MIT licensed, copyright 2026 Daniel Tremer. The architectural inspiration is [ScreenQuest](https://github.com/DanielTea/screenquest), also MIT; the new runner does not import its local game sessions or assets.

ViZDoom, its engine components, scenarios and bundled game assets are separate third-party works. They are installed from the pinned upstream distribution and retain their upstream licenses: consult [ViZDoom](https://github.com/Farama-Foundation/ViZDoom) and the licenses included in that distribution. Screenshots in evaluation evidence are game-rendered output, not relicensed as original MIT artwork. No proprietary Doom WADs or other commercial game packages are redistributed by this repository.

NumPy, Pillow, pytest, Ruff, Python, model clients and other dependencies retain their own licenses. `uv.lock` records dependency versions. Astra and Claude are hosted proprietary models, accessed through the account's existing authenticated clients; no model weights or credentials are distributed.

The site uses Google Fonts (JetBrains Mono, Orbitron and Rajdhani), fetched by the browser. If that service is unavailable, system sans-serif fonts are used. Game names and trademarks belong to their owners; listing a candidate does not imply affiliation, endorsement, licensing or automation permission.

Environment screenshots, clips and the screenshot collage contain third-party game imagery and are not covered by the original-code MIT license. See [media credits and sources](MEDIA.md).

## Optional integrations added in 0.2

These packages are installed separately; their licenses do not become MIT merely because the adapter is MIT. Consult the pinned upstream distribution for full notices and asset-specific terms:

- [Procgen](https://github.com/openai/procgen): engine and included asset notices.
- [Crafter](https://github.com/danijar/crafter), [MiniWorld](https://github.com/Farama-Foundation/Miniworld), [PettingZoo](https://github.com/Farama-Foundation/PettingZoo): engine, dependencies and image assets.
- [NLE](https://github.com/facebookresearch/nle) and [MiniHack](https://github.com/facebookresearch/minihack): wrappers and NetHack source/tiles have separate upstream notices.
- [ALE](https://github.com/Farama-Foundation/Arcade-Learning-Environment): emulator/package license is separate from Atari game rights. No ROM files are added to this repository.
- [Stable-Retro](https://github.com/Farama-Foundation/stable-retro): emulator/core licenses and the bundled Airstriker demo's upstream distribution terms. No other ROMs are used.
- [PySuperTuxKart2](https://github.com/bpiwowar/pystk2): upstream README identifies GPL licensing; package metadata's MIT classifier must not be treated as overriding its actual GPL source notices. Its downloaded assets retain their own licenses. The admitted Linux ARM64 task uses the explicit deterministic-render-v1 GPL derivative patch; see [full engine notices](../environments/docker-stk/COPYING).
- [Unity ML-Agents](https://github.com/Unity-Technologies/ml-agents): the admitted VisualFoodCollector adapter uses a separately downloaded official example executable; engine, example assets and redistribution terms remain upstream. No executable is committed; it is installed separately and pinned by digest.
- [MLX VLM](https://github.com/Blaizzy/mlx-vlm): inference code and each separately cached model have their respective licenses. No model weights or cached custom processor code are redistributed here.

The Hugging Face Dataset export contains measurements only. The optional static Space includes the same credited game previews as the website; check `media/NOTICE.txt` and `media/sources.json` before republication. Game binaries, assets and provider credentials are not part of either export.

## Integrations added in 0.3

[Google Research Football](https://github.com/google-research/football/tree/ba9952130898bde2879b01ff2b49d3d48d26ce81), its native engine, fonts and assets retain their upstream licenses; the source is built locally into a separately installed image. The repository contains adapter/build instructions, not a redistribution of its compiled game.

The [SuperTuxKart simulation-clock patch](../environments/docker-stk/simulation-clock.patch) is derivative GPL-3.0-or-later engine code, excluded from the original benchmark's MIT license. Its [COPYING](../environments/docker-stk/COPYING) preserves upstream source and asset notices. The official assets are downloaded and checksum-verified separately. Neither engine image nor asset archive is included in the evidence or Hugging Face exports.

[Luanti/Craftium](https://github.com/mikelma/craftium/tree/8cffe4176e793f78d00b17fa7e46ccf333a7b5b0) uses a separate native Linux ARM64 build. The [lockstep patch](../environments/docker-craftium/lockstep.patch) changes LGPL-2.1-or-later engine source; its [license](../environments/docker-craftium/COPYING.LESSER) and [asset notices](../environments/docker-craftium/COPYING) remain applicable. Upstream README summaries do not override individual source-file licenses. minetest_game and individual mods and textures retain their own terms. No engine binary or world database is included in the benchmark repository or public evidence.

[SuperTux](../environments/docker-supertux/README.md), [Dungeon Crawl Stone Soup](../environments/docker-crawl/README.md), [OpenTTD](../environments/docker-openttd/README.md), [Mindustry](../environments/docker-mindustry/README.md), [Cataclysm: DDA](../environments/docker-cdda/README.md) and [Warzone 2100](../environments/docker-warzone/README.md) are separately built native engines. Their derivative patches retain the licenses identified in those directories; the benchmark's MIT license does not supersede them. In particular, Cataclysm: DDA retains its CC BY-SA 3.0 source/content terms, and Warzone preserves both GPL and separately licensed component/asset notices. Native screenshots are attributed game output, not original MIT artwork.

The unadmitted [StarCraft II probe](../environments/experimental-sc2/README.md) requires Blizzard's separately downloaded research client and DeepMind mini-game maps. It does not redistribute those files. The unadmitted [Veloren prototype](../environments/experimental-veloren/README.md) includes a derivative GPL source patch and upstream license, but no compiled engine or Git LFS assets.

The unadmitted [0 A.D. prototype](../environments/experimental-0ad/README.md) retains GPL-2.0-or-later engine source terms and the upstream [source and asset notices](../environments/experimental-0ad/LICENSE.md). Separately downloaded game data is not included.
