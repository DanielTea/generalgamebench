# SuperTuxKart runtime

Task `supertuxkart-lighthouse` version 3 uses PySuperTuxKart2 0.7.4 with patch
`deterministic-render-v2`. It uses the official SuperTuxKart 1.5 assets and Mesa
software rendering. The runtime supports Linux ARM64 and Linux x86_64. A Mac
uses its native ARM64 image through Docker Desktop.

```sh
uv run --no-sync python environments/docker-stk/install.py
GGBENCH_RUN_INTEGRATION=1 uv run --no-sync pytest tests/test_integrations.py -k supertuxkart -q
```

The installer checks the engine revision, source patch, and asset checksums.
It keeps the assets outside the image and mounts them read-only. The engine
has no network access. Each architecture has a separate image identity.
Both images use one renderer thread and 128-bit vectors. Mesa documents this
setting in its [LLVMpipe guide](https://docs.mesa3d.org/drivers/llvmpipe.html).

The patch stops the Irrlicht wall clock. It advances animation and material
wind with the physics clock. It preserves scene registration order. It also
sorts shader names, texture keys, and mesh creation IDs before drawing.
This prevents memory addresses from selecting which object wins a depth tie.
The referee uses the complete native image. It does not mask or round pixels.

A long random-control test found a one-pixel difference in the earlier shader
renderer. Version 2 of the patch adds a stable order to that rendering path.
Earlier results retain task version 2 and their original image identity.
Do not replace their metadata with the new version.

The task starts with 50 neutral steps. A valid action advances 0.2 seconds.
The score is native forward distance divided by track length, limited to [0, 1].
The negative start sentinel cannot award a lap. Tests cover driving, random
controls, wait, rescue, and exact image and score replay.

The upstream engine and this patch use GPL-3.0-or-later. Bundled components and
assets retain their separate notices. See [COPYING](COPYING) and the pinned
[upstream source](https://github.com/bpiwowar/pystk2/tree/dd70f6823f248ae1df2ce513839a9b2c8c940c39).
The benchmark MIT license does not replace these terms.
