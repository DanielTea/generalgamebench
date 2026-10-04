# Additional Mac integration attempts

These diagnostics are not leaderboard entries. The 45-card catalog distinguishes validated tasks from candidate integrations.

## SuperTuxKart

The unmodified PySuperTuxKart2 0.7.4 Mac runtime loaded official 1.5 assets and accepted driving controls, but rendered animation pixels diverged across seeded processes. Physics rewards alone were repeatable. A diagnostic native ARM64 rebuild still failed the pixel gate, so neither Mac path is admitted.

Task version 2 uses a documented `deterministic-render-v1` source patch: stop the Irrlicht wall clock, advance it from physics ticks, and route material wind through that clock. With Linux ARM64 Mesa rendering, 200 controls reproduced all 201 rendered frames, final progress and metadata across fresh containers, including deliberately varied delays before actions. A broader random-control run at seed 5001 then exposed four isolated tree-edge pixels with process-dependent depth ties. Preserving solid scene registration order instead of sorting by texture pointer addresses fixes that path. The camera is not masked. A fixed 50-decision neutral pre-roll settles the starting introduction. Separate wait/rescue tests cover the engine's negative starting-distance sentinel, which must not award a lap. [Reproducible build and patch](../environments/docker-stk/README.md).

## Luanti / Craftium

The official Craftium 0.0.1 x86_64 wheel initially crashed before connecting to its Python referee under Docker on this Mac. A native Linux ARM64 build from official `pkg` source commit `8cffe4176e793f78d00b17fa7e46ccf333a7b5b0` launches Luanti 5.12.0 and returns real 64×64 RGB frames with SDL offscreen/Mesa rendering.

The unpatched native build completed two 600-action `ChopTree-v0` runs at seed 71, but 532 of their 601 camera frames differed. Fixing client/server/render time and synchronizing server and mesh updates removed the major drift. Broader tests exposed address-dependent draw order, shared cosmetic randomness and the upstream weather mod's wall-clock/session-random cloud parameters. The `serial-lockstep-v2` variant preserves draw order, uses one mesh thread, seeds particles and cloud generation independently, and uses the upstream fixed-weather setting. Two delayed 600-action diagnostic trajectories then reproduce all 601 images and rewards. The final packaged worker passed all three admission tests, including the rewarded route and the 600-action delayed replay. No image tolerance or masking is used.

The admitted `luanti-chop-tree` task uses the pinned snowy forest and steel axe, and ends when the native Lua referee awards the first tree-node reward, at native death, or the declared horizon. A known control sequence chops a tree block after 50 decisions. The upstream task normally continues collecting resources; this one-tree objective is an explicit bounded benchmark variant. Coordinates, velocity, camera angles, engine time and voxel state remain private. [Pinned build, task and license details](../environments/docker-craftium/README.md).

## Google Research Football

The engine is built from official version 2.10.2 source at `ba9952130898bde2879b01ff2b49d3d48d26ce81` for Linux ARM64. Headless EGL rendering works under Docker Desktop on this Mac. The admitted `football-empty-goal` task uses only the native pixels wrapper and goal reward in `academy_empty_goal_close`, without checkpoint shaping or state inputs to the participant.

A known control sequence scores a goal and terminates after 17 decisions; all 18 frames and scores repeat in fresh containers. Two random-control episodes at seeds 5000 and 5001 also score and terminate through the full referee and replay verifier. Held direction and shot inputs are released before each new decision, so wait is neutral. [Runtime and scope](../environments/docker-football/README.md).

## Unity

The [official ML-Agents registry](https://unity-technologies.github.io/ml-agents/Unity-Environment-Registry/) points to a prebuilt Mac example bundle. Both GridWorld and VisualFoodCollector launched through ML-Agents 1.1.0 under Python 3.10.12. GridWorld also has a private goal vector, so the chosen candidate is VisualFoodCollector with only its native RGB camera. Structured vectors and action masks remain referee-only. Pin the exact executable and assets; generated profiler timer logs are excluded from the input asset digest.

VisualFoodCollector is now admitted as `unity-food-collector`. A 178-action seed-2 trajectory collects positive food and reproduces all 179 camera frames plus raw/normalized rewards across fresh workers. Two 200-decision random-control episodes (seeds 5000 and 5001) also collect food through the full referee and replay verifier. The pinned native reward is +1 for green food and −1 for red food, normalized against a fixed ten-net-food target. Private vectors and rewards stay out of observations. The frozen v0.2 rankings remain a 33-task cohort and do not contain this newly admitted scene.

## SuperTux

The official 0.6.3 source runs with SDL software rendering at 640×480. A small published patch supplies seeded input boundaries and advances eight native 15 ms physics steps per action. The task uses the original Welcome to Antarctica level and ends at its first native coin, player death, or the horizon. A 12-decision jump/run route earns a coin; an idle route dies after 101 decisions. Both routes and a 24-decision control check reproduce their complete frames, scores, termination and metadata across independent workers. [Build and scope](../environments/docker-supertux/README.md).

## Dungeon Crawl Stone Soup

The 0.34.0 tile build starts a native Minotaur Fighter on Dungeon:1. The task ends at first earned experience, death, or horizon. Only ordinary direction, wait, confirm and cancel keys are available. Native floor-decoration hashing used character creation wall time; the published patch derives it from the game seed. A 24-key combat route earns native experience, and an 80-wait seed-zero check covers the engine's special unseeded-zero convention. All three admission tests reproduce exact cameras and results. [Build and scope](../environments/docker-crawl/README.md).

## OpenTTD

Official 15.3 runs its native 32-bit software renderer and OpenGFX 7.1 assets at 800×600. The task is to construct the first owned road on a seeded 64×64 map, using the normal road toolbar and mouse controls. The referee reads native company-owned road bits; it does not execute construction commands. A seven-action route builds a road, and a longer random-input test exercises the interface. All three final worker tests passed exact replay. [Build and scope](../environments/docker-openttd/README.md).

## Mindustry

The official v160.5 client and pinned Arc SDL runtime render Ground Zero at 960×640. The task is to mine 15 copper using ordinary movement and mouse input. The official client archive lacks an ARM64 SDL library, so the installer builds it from the pinned Arc source. Fixed native frames and seeded initialization let model response time remain outside game progression. The final worker passes the general input/replay check and a 43-decision rewarded mining route, with all frames and native copper counts reproduced despite delayed inputs. [Build and scope](../environments/docker-mindustry/README.md).

## Cataclysm: Dark Days Ahead

Official 0.I-1 runs the native tutorial with UltimateCataclysm tiles and its original preset character. Ordinary movement, tutorial dismissal and native inventory keys reach and wield the baseball bat after 49 decisions. Both final worker tests passed, including exact images, score, termination and metadata in a fresh process with delayed inputs. The adapter never moves the player or equips an item directly. [Build and bounded task](../environments/docker-cdda/README.md).

## Warzone 2100

Official 4.7.0 runs its original TUTORIAL3 base-building scenario with native SDL3/OpenGL rendering. Standard truck selection and oil-resource clicking complete the first derrick after 41 decisions. Both final worker admission tests passed exact replay with delayed inputs. The source patch uses fixed native ticks and corrects the tutorial's global-context lookup for the shipped QuickJS configuration. Private scoring reads completed native structures, without issuing build commands. [Build and bounded task](../environments/docker-warzone/README.md).

## Crafter replay correction

The full evidence audit found a version-1 Crafter frame mismatch at tick 11 for seed 4001. The upstream engine balances creature populations every ten ticks using an address-hashed object set. Sorting that set by unique tile position before balancing removes this process-dependent choice. A 132-action regression now repeats exact frames and score across four fresh workers. All 33 Crafter episodes (every model and both reference cohorts) are regenerated under task version 2; the original version-1 episodes remain local diagnostic evidence and are excluded uniformly, regardless of score.

## StarCraft II — native scoring works, visual replay unresolved

The official 4.10.0.75689 Linux research client runs on this Mac through Docker/Rosetta with Mesa OSMesa. The original MoveToBeacon map supplies native RGB; ordinary army selection and minimap Smart commands reach its first beacon after 25 decisions. Native game-loop counts and score reproduce across two fresh runs with delayed input, but all 26 RGB frames differ around animated objects. Fixed wall-clock, fixed-seed startup and low-graphics trials also fail the visual gate. No debug or raw-entity commands are used. This remains an unadmitted [reproducible diagnostic](../environments/experimental-sc2/README.md), outside every leaderboard.

## Veloren — native control loop works, admission unfinished

Official source `f6294887b13b287160d2de75809675ee521f65f4` builds with its pinned Rust nightly, loads the native single-player world and character, and renders through Vulkan under Linux ARM64 on this Mac. A published prototype supplies server/frontend synchronization, fixed ticks, ordinary movement/interaction and native camera capture. Two ten-decision traces both return 11 frames, but all frames differ; startup, asynchronous terrain preparation and remaining randomness need investigation. A rewarded collection route has not been verified. See the [prototype and exact limitations](../environments/experimental-veloren/README.md).

## 0 A.D. — native task works, renderer admission unfinished

Official 0.28.0 launches a seeded Mainland map and the ordinary selection/right-click route gathers ten wood after 246 decisions. Fixed simulation/render/LOS/minimap clocks and stable draw order improve replay. An uninitialized GUI sprite rounding flag caused nondeterministic one-pixel shifts; initializing it removed the large emblem/minimap differences. A separate native fix avoids NaN texture coordinates for solid-color UI sprites. Two initial images still differ at 661 world pixels, even though model order, transforms, mesh coordinates/normals, colors and static material uniforms match. The final cleaned-build goal pair agrees on every wood count through decision 246, but all 247 images differ (28 initial world pixels in that pair). The [source patch and reproducible probe](../environments/experimental-0ad/README.md) remain unadmitted; no image tolerance or masking changes the acceptance criteria.
