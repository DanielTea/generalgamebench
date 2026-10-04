# Third-party notices

Original GeneralGameBench code is MIT licensed, copyright 2026 Daniel Tremer. The architectural inspiration is [ScreenQuest](https://github.com/DanielTea/screenquest), also MIT; the new runner does not import its local game sessions or assets.

ViZDoom, its engine components, scenarios and bundled game assets are separate third-party works. They are installed from the pinned upstream distribution and retain their upstream licenses: consult [ViZDoom](https://github.com/Farama-Foundation/ViZDoom) and the licenses included in that distribution. Screenshots in evaluation evidence are game-rendered output, not relicensed as original MIT artwork. No proprietary Doom WADs or other commercial game packages are redistributed by this repository.

NumPy, Pillow, pytest, Ruff, Python, model clients and other dependencies retain their own licenses. `uv.lock` records dependency versions. Astra and Claude are hosted proprietary models, accessed through the account's existing authenticated clients; no model weights or credentials are distributed.

The site uses Google Fonts (DM Sans and Space Grotesk), fetched by the browser. If that service is unavailable, system sans-serif fonts are used. Game names and trademarks belong to their owners; listing a candidate does not imply affiliation, endorsement, licensing or automation permission.

Environment screenshots, clips and the screenshot collage contain third-party game imagery and are not covered by the original-code MIT license. See [media credits and sources](MEDIA.md).

## Optional integrations added in 0.2

These packages are installed separately; their licenses do not become MIT merely because the adapter is MIT. Consult the pinned upstream distribution for full notices and asset-specific terms:

- [Procgen](https://github.com/openai/procgen): engine and included asset notices.
- [Crafter](https://github.com/danijar/crafter), [MiniWorld](https://github.com/Farama-Foundation/Miniworld), [PettingZoo](https://github.com/Farama-Foundation/PettingZoo): engine, dependencies and image assets.
- [NLE](https://github.com/facebookresearch/nle) and [MiniHack](https://github.com/facebookresearch/minihack): wrappers and NetHack source/tiles have separate upstream notices.
- [ALE](https://github.com/Farama-Foundation/Arcade-Learning-Environment): emulator/package license is separate from Atari game rights. No ROM files are added to this repository.
- [Stable-Retro](https://github.com/Farama-Foundation/stable-retro): emulator/core licenses and the bundled Airstriker demo's upstream distribution terms. No other ROMs are used.
- [PySuperTuxKart2](https://github.com/bpiwowar/pystk2): upstream README identifies GPL licensing; package metadata's MIT classifier must not be treated as overriding its actual GPL source notices. Its downloaded assets retain their own licenses. This integration is experimental and excluded from scored suites.
- [MLX VLM](https://github.com/Blaizzy/mlx-vlm): inference code and each separately cached model have their respective licenses. No model weights or cached custom processor code are redistributed here.

The Hugging Face Dataset export contains measurements only. The optional static Space includes the same credited game previews as the website; check `media/NOTICE.txt` and `media/sources.json` before republication. Game binaries, assets and provider credentials are not part of either export.
