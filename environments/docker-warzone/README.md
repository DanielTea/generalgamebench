# Warzone 2100 — first oil derrick

`warzone-first-derrick` runs the original TUTORIAL3 base-building tutorial in Warzone 2100 4.7.0. Select a construction truck and click an oil resource to construct a derrick. The first native completed structure scores one and ends the task. Losing both trucks or reaching the horizon ends an unsuccessful attempt. This is an introductory construction task, not a campaign or multiplayer match score.

```sh
uv run python environments/docker-warzone/install.py
GGBENCH_RUN_INTEGRATION=1 uv run pytest tests/test_integrations.py -k warzone -q
```

The complete native 960×640 SDL3/OpenGL view is captured under Xvfb and Mesa. A source patch advances the native clock by 100 ms per action and waits at the input boundary. Forty initial frames load the scene. Cursor directions move 32 pixels, fine directions move eight, and clicks and menu keys enter the ordinary native input handlers. The pointer begins at screen center. The referee privately reads the native completed-structure and lost-unit counters; it never issues construction commands. Only pixels and legal control names reach the participant.

The patch also replaces the tutorial script's disabled dynamic `Function` call with `globalThis`, preserving its global-context lookup under the shipped QuickJS configuration. It does not enable script evaluation or change the tutorial objective. No camera region is removed or replaced.

A 41-decision route builds the first oil derrick. Both final worker admission tests pass exact image, score, termination and metadata replay, including deliberately delayed inputs.

The installer verifies the game revision, recursive submodule revisions, source patch, generated revision cache and SDL3 3.2.26 source archive. It builds Linux ARM64 for Docker Desktop, with external networking disabled during evaluation, a read-only root and a temporary configuration directory. Evidence records the immutable image ID; local runs remain unattested.

The engine and source changes retain their [GPL terms](COPYING), [additional terms](COPYING.NONGPL) and [upstream notices](COPYING.README). Assets keep their original licenses. The benchmark's MIT license does not relicense the game, and evidence/Hugging Face exports contain no game binary.
