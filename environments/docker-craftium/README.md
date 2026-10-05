# Luanti: chop one tree block

For Linux x86_64, use the [full-suite installer](../linux/README.md). The installer selects an AMD64 image on that platform. Apple Silicon uses the existing ARM64 image.

`luanti-chop-tree` uses the official Craftium ChopTree world and native 64×64 Luanti camera. It runs a Linux ARM64 source build on this Mac through Docker Desktop. The explicit `serial-lockstep-v2` engine patch is required; the upstream asynchronous runtime does not pass exact camera replay.

```sh
uv run python environments/docker-craftium/install.py
GGBENCH_RUN_INTEGRATION=1 uv run pytest tests/test_integrations.py -k luanti -q
uv run generalgamebench run --agent random --games luanti-chop-tree --seeds 2 --start-seed 5000 --steps 200 --mode exhibition --output runs/luanti-example
```

The agent starts with a steel axe in a pinned snowy forest. Eight controls are available: wait, forward, jump, dig, look right, look left, look up and look down. They use the official discrete wrapper, including its 0.5 mouse magnitude. One action advances 0.02 simulated seconds, after the upstream 200-frame initialization. The native Lua referee awards one for digging a tree node. This bounded benchmark task ends on the first such reward, native death, or the declared horizon. A goal scores one; otherwise zero. It is not the upstream unrestricted resource-collection metric or a general Minecraft replacement.

The participant sees only the native RGB camera and control instructions. Craftium's player coordinates, velocity, camera angles, voxel arrays and engine time never enter its observations. Initial world data is a fixed upstream snapshot, not a newly generated world per seed. The supplied reset seed controls map generation and Lua randomness where used.

The engine patch fixes client and server physics time, advances rendering time from simulation ticks, waits for the server's update before letting the client continue, and waits for pending mesh generation before displaying the next scene. Mesh generation uses one thread. Scene/material traversal preserves registration order rather than pointer-address order. Native particle and cloud generation use separate seeded randomness. The upstream `enable_weather=false` setting disables the weather mod, whose wall-clock updates and session-random offset otherwise change cloud pixels; the ordinary native cloud renderer remains enabled. This makes the supported task independent of variable agent response delays. The admission checks include a 50-action tree reward and 600 actions without a reward, comparing every native image, score and metadata field across new processes. No image regions are masked and no tolerance replaces the exact replay gate.

Source and game submodule revisions, patch digest and the base image are pinned. Episodes record the actual immutable built image ID. Keep that image for replay: rebuilding with different distribution system packages can produce a different ID. Game binaries and maps are built/downloaded separately; they are not part of the evidence or Hugging Face exports. The trusted engine container has no external network, a read-only root filesystem, temporary world copies, and only referee source mounted from the host. Its temporary filesystem allows execution because Craftium copies the pinned Luanti executable beside each world before launching it. Local evidence remains unattested.

Luanti engine changes retain their LGPL-2.1-or-later source terms. Craftium, minetest_game, individual mods, textures and sounds retain their own upstream licenses. [COPYING](COPYING) preserves asset notices and [COPYING.LESSER](COPYING.LESSER) provides the engine license; [upstream source and notices](https://github.com/mikelma/craftium/tree/8cffe4176e793f78d00b17fa7e46ccf333a7b5b0) govern the separately built runtime. The benchmark's MIT license does not relicense those works.
