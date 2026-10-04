# Game feasibility catalog

Reviewed 2026-10-04. **10 runnable scenarios across 3 game families; 42 researched candidates/families.** A candidate is not a supported title or a promise of permission to automate. Family entries overlap potential individual titles and must not be presented as a total count of unique games.

The implementation uses two original 2D games and eight ViZDoom scenarios. ViZDoom is based on the 1993 Doom engine; it is not a modern AAA integration. Modern 3D and AAA expansion is explicit future work.

| Environment | Category | Status | Feasibility / remaining work |
| --- | --- | --- | --- |
| [Coin Run](https://github.com/DanielTea/screenquest-arena) | ORIGINAL · 2D | runnable | Collect coins using only rendered pixels. Seeded 10×10 world; fixed-horizon score. |
| [Dodge Lanes](https://github.com/DanielTea/screenquest-arena) | ORIGINAL · 2D | runnable | Avoid falling obstacles. Two local visual policies and controls are included. |
| [ViZDoom · eight scenarios](https://github.com/Farama-Foundation/ViZDoom) | DOOM ENGINE · 3D | runnable | Basic, defend center, defend line, take cover, health gathering, corridor, home and prediction. These are eight scenarios of one game family. |
| [SuperTuxKart](https://github.com/supertuxkart/stk-code) | OPEN SOURCE · 3D RACING | candidate | Strong next candidate: controlled tracks, lap timing, renderer capture and deterministic resets need an adapter. |
| [Luanti](https://github.com/luanti-org/luanti) | OPEN SOURCE · 3D SANDBOX | candidate | Modern voxel engine. Pin one game/modpack and separate referee-only Lua events from agent pixels. |
| [Veloren](https://gitlab.com/veloren/veloren) | OPEN SOURCE · 3D RPG | candidate | Private test worlds are a promising route. Combat scoring and reproducible resets remain research work. |
| [Warzone 2100](https://github.com/Warzone2100/warzone2100) | OPEN SOURCE · 3D RTS | candidate | Use offline skirmishes, fixed maps and native replay/result verification. Visual-control adapter required. |
| [0 A.D.](https://gitea.wildfiregames.com/0ad/0ad) | OPEN SOURCE · 3D RTS | candidate | Pin engine and map. Build an offline referee adapter; do not expose omniscient simulation data to the agent. |
| [SuperTux](https://github.com/SuperTux/supertux) | OPEN SOURCE · 2D PLATFORMER | candidate | Local levels make reset, completion and survival scoring plausible. Adapter not implemented. |
| [Mindustry](https://github.com/Anuken/Mindustry) | INDIE · 2D STRATEGY | candidate | Open-source game with private scenarios. Score objectives externally; keep scripting and state APIs referee-only. |
| [OpenTTD](https://github.com/OpenTTD/OpenTTD) | OPEN SOURCE · 2D SIMULATION | candidate | Fixed maps and scenario goals. Requires long-horizon scoring and a separate planning-oriented division. |
| [NetHack](https://github.com/facebookresearch/nle) | ROGUELIKE · 2D | candidate | NLE offers a research interface. Use rendered observations; terminal-symbol and state tracks must be separate. |
| [MiniHack](https://github.com/facebookresearch/minihack) | RESEARCH · 2D | candidate | NLE-based skill tasks. Archived upstream; installation/version compatibility needs validation. |
| [Dungeon Crawl Stone Soup](https://github.com/crawl/crawl) | ROGUELIKE · 2D | candidate | Open-source turn-based game. Tile capture and deterministic task/reset support need development. |
| [Cataclysm: Dark Days Ahead](https://github.com/CleverRaven/Cataclysm-DDA) | SURVIVAL · 2D | candidate | Long-horizon planning and survival candidate. Requires pinned saves, visual interface and auditable objectives. |
| [Crafter](https://github.com/danijar/crafter) | RESEARCH · 2D SURVIVAL | candidate | Achievement-based generalization tasks. An RGB adapter and achievement normalization remain to be implemented. |
| [MiniWorld](https://github.com/Farama-Foundation/Miniworld) | RESEARCH · 3D | candidate | Lightweight navigation environments. RGB rendering and platform-specific graphics setup need validation. |
| [Unity ML-Agents environments](https://github.com/Unity-Technologies/ml-agents) | MODERN ENGINE · 3D / 2D | candidate | Custom Unity games can offer rendered cameras and independent referees. SDK support does not make arbitrary Unity titles controllable. |
| [Google Research Football](https://github.com/google-research/football) | RESEARCH · 3D SPORT | candidate | Controlled football tasks. Keep raw state-based agents in a separate track from rendered-pixel agents. |
| [Minecraft](https://github.com/minerllabs/minerl) | COMMERCIAL · 3D SANDBOX | candidate | MineRL/Malmo are established research routes, with version and installation constraints. Requires a lawful game setup and adapter. |
| [StarCraft II](https://github.com/Blizzard/s2client-api) | AAA · 3D STRATEGY | candidate | Official SC2 API and PySC2 provide a strong offline candidate. Feature layers and privileged state cannot enter the pixels-only track. |
| [Rocket League / RocketSim](https://github.com/RLGym/rlgym) | COMMERCIAL · 3D SPORT | candidate | RLGym is a research route. Simulator and retail-game results must be distinct; visual capture and access constraints need validation. |
| [Factorio](https://lua-api.factorio.com/latest/) | INDIE · 2D AUTOMATION | candidate | Official Lua API can implement a trusted referee. Agents would receive screenshots only. Game license and deterministic scenario needed. |
| [Cyberpunk 2077](https://www.cyberpunk.net/en/modding-support) | AAA · MODERN 3D | candidate | Official REDmod exists. A repeatable offline benchmark is exploratory, requires licensed installs, hardware and task/referee work. |
| [Morrowind / OpenMW](https://github.com/OpenMW/openmw) | COMMERCIAL ASSETS · 3D RPG | candidate | Open-source engine is a viable integration route; original game assets require separate rights. Scripted tasks and capture not implemented. |
| [Half-Life 2 / Source SDK](https://github.com/ValveSoftware/source-sdk-2013) | AAA · 3D FPS | candidate | Source SDK offers an offline research path. Game assets and SDK terms remain separate; full adapter and validation needed. |
| [Atari / Arcade Learning Environment](https://github.com/Farama-Foundation/Arcade-Learning-Environment) | RETRO · 2D FAMILY | candidate | Large established benchmark family. ROM permissions and pixel/action parity must be checked per title; not integrated. |
| [Stable-Retro library](https://github.com/Farama-Foundation/stable-retro) | RETRO · 2D FAMILY | candidate | Potential multi-console coverage. No copyrighted ROMs are bundled; verify each integration and its game assets. |
| [PettingZoo environments](https://github.com/Farama-Foundation/PettingZoo) | MULTI-AGENT · 2D FAMILY | candidate | Good route to simultaneous multi-agent competition. RGB-only support and outcome definitions must be checked environment by environment. |
| [Procgen / BigFish](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / BossFight](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / CaveFlyer](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / Chaser](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / Climber](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / CoinRun](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / Dodgeball](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / FruitBot](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / Heist](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / Jumper](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / Leaper](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / Maze](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / Miner](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / Ninja](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / Plunder](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |
| [Procgen / StarPilot](https://github.com/openai/procgen) | PROCEDURAL · 2D | candidate | Research candidate from the 16-environment Procgen suite. Legacy package compatibility needs work; no adapter or measured result yet. |

## Admission gates

Every adapter must document a permitted execution setup, asset licenses, reproducible reset/seed policy, engine/build hashes, public controls, observation channel, independent score extraction, episode termination and replay checks. Pin the exact task before admitting scores. No public multiplayer farming, anti-cheat bypass, memory scraping by participants, or redistribution of proprietary assets.

## Suggested integration order

1. SuperTuxKart, Crafter, Luanti and MiniWorld: diverse environments with accessible source or research interfaces.
2. StarCraft II, Minecraft and Factorio: richer tasks with game-specific setup and referee engineering.
3. Modern AAA offline tasks such as Cyberpunk 2077: dedicated licensed machines, stable save states, score adjudication and much higher operational cost.

These priorities are engineering judgments from the linked primary projects; availability of source or a mod API does not establish legal permission for every intended use.
