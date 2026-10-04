# SuperTux: collect the first coin

`supertux-first-coin` runs the real SuperTux 0.6.3 engine and its official **Welcome to Antarctica** level. The native SDL software renderer supplies the full 640×480 RGB image. The Python participant has no access to player coordinates, object lists, scripts, saves or the native coin counter.

```sh
uv run python environments/docker-supertux/install.py
GGBENCH_RUN_INTEGRATION=1 uv run pytest tests/test_integrations.py -k 'supertux and not supertuxkart' -q
uv run generalgamebench run --agent random --games supertux-first-coin --seeds 2 --start-seed 5000 --steps 200 --mode exhibition --output runs/supertux-example
```

The task starts a fresh player/save directly in the level, skipping the introduction menu and fades. Nine controls expose wait, left, right, jump, jumping left/right, running right, running and jumping right, and duck. Each decision holds its controls for up to eight native 15 ms physics ticks. The first native level coin ends the task and scores one. Native death scores zero and ends before automatic respawn; a declared decision horizon also ends play. This is an explicit first-coin objective, not full-level completion.

The `native-lockstep-v1` source patch adds the blocking referee channel, native framebuffer capture before presentation, fixed physics advancement and initial seed selection. It does not move the player, collect coins, reveal state to the participant, or replace the level with a recreation. A small missing C++ header is also supplied for the pinned compiler. Audio is disabled; gameplay textures and mechanics are upstream.

A known run/jump sequence reaches a coin after 12 decisions. An idle sequence dies after 101. The admission checks compare every image, raw reward, normalized score and metadata field in fresh containers, including varied action delays. The image ID, source revision and variant are recorded in each episode. Keep the exact built image for replay; changes to distribution system packages can change its immutable ID.

Docker Desktop must be running. The build uses pinned source and five pinned submodules, with game assets inside the resulting Linux ARM64 image. The runtime has no external network, a read-only root filesystem, temporary saves and only referee source mounted from the host. These are trusted local engine tests, not a hostile-agent competition service.

The SuperTux engine changes retain [GPL-3.0-or-later terms](LICENSE.txt). The external partio_zip header change and game assets retain their original individual notices in the [pinned upstream source](https://github.com/SuperTux/supertux/tree/c1ddb4f28c54de77f07aa9965231a91c0ed06708). The benchmark's MIT license does not relicense those works. No engine binary or game asset bundle is committed or included in evidence/Hugging Face exports.
