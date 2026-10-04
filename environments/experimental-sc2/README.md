# StarCraft II diagnostic — not admitted

The official free research client **4.10.0.75689**, data revision `B89B5D6FA7CBF6452E721311BFBC6CB2`, runs on this Apple Silicon Mac through Linux x86_64 Docker/Rosetta and Mesa OSMesa. `MoveToBeacon` returns its native 640×480 RGB camera and 128×128 RGB minimap. The probe places those unaltered images side by side on a 768×480 canvas. No feature-layer or raw entity state is exported as agent input.

Native army selection and minimap Smart commands reached the beacon after 25 decisions and earned the game's score of 1. The same route with delayed decisions reproduced native game-loop counts and scores, but **all 26 rendered frames differed** around the animated marine and beacon. Fixed wall time, the native fixed-seed options and the low graphics preset did not resolve exact visual replay. This diagnostic is deliberately absent from the task registry and all standings.

The [official protocol](https://github.com/Blizzard/s2client-proto/blob/master/s2clientprotocol/sc2api.proto) marks RGB `action_render` as unimplemented. The probe therefore enables the feature interface privately for ordinary minimap commands. It uses `action_ui.select_army` and `action_feature_layer.unit_command`, never raw unit IDs or debug/game-state mutations. The minimap command coordinates are those of that interface; they must not be represented as direct RGB-screen clicks. The [official interface description](https://github.com/Blizzard/s2client-proto/blob/master/docs/protocol.md) distinguishes these interfaces.

## Reproduce the diagnostic

Obtain the pinned client from `diagnostic.json` using the [official Linux installation instructions and license](https://github.com/Blizzard/s2client-proto/blob/master/docs/linux.md). The official archive is password-protected with its published installation acknowledgement. Check its SHA-256 before extraction. Install the pinned DeepMind mini-games archive into `StarCraftII/Maps/mini_games` and make `Versions/Base75689/SC2_x64` executable. Game files are not redistributed by this repository.

From the repository root, with that installation at `.game-assets/sc2-4.10/StarCraftII`:

```sh
docker build --platform linux/amd64 -t ggbench-sc2:diagnostic environments/experimental-sc2
mkdir -p .game-cache/sc2-diagnostic
docker run --rm --init --platform linux/amd64 --network none \
  -e TAG=first -e SEED=71 -e 'ACTIONS=[5,2,2,2,2,2,3,10,10,9,9,6,0,0,0,0,0,0,0,0,0,0,0,0,0]' \
  -v "$PWD/.game-assets/sc2-4.10/StarCraftII:/assets:ro" \
  -v "$PWD/.game-cache/sc2-diagnostic:/out" \
  -v "$PWD/environments/experimental-sc2/probe.py:/probe.py:ro" \
  ggbench-sc2:diagnostic /probe.py
```

Repeat with `TAG=replay` and `DELAY=0.1`, then compare the JSON frame hashes and native scores. Controls are wait (0), minimap cursor up/right/down/left by eight units (1–4), select army (5), Smart command at cursor (6), and two-unit fine cursor movement (7–10). Cursor starts at (64,64); each decision advances eight game loops. A successful run ends at the first positive score.

Before admission: establish a reproducible native RGB variant; map and document the visual/control geometry; package the final worker with immutable runtime and asset digests; verify exact full-referee replay, goal and no-progress cases. Cosmetic discrepancies are not masked or accepted with a tolerance. This probe is trusted local development code, not a hostile-participant runner.

The probe's original code is MIT. Blizzard game assets and binaries remain governed by Blizzard's terms; the protocol package retains its upstream license. A future Hugging Face export must contain benchmark evidence and manifests, not the game installation.
