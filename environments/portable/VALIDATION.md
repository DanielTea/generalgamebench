# Portable runner 0.4.0

The published multi-architecture image is pinned in `image.txt`:

```text
ghcr.io/danieltea/generalgamebench@sha256:1fabc2750c87ba08f4429715b2e7a07b36c20464d554744eba1164d9bda4eb2a
```

It contains Linux AMD64 and Linux ARM64 images built from source revision `9a22a0af1a56ce4f09284b760ba99adec0376e1f`. An unauthenticated registry request successfully retrieved both platform manifests on 2026-10-05. No GitHub login or registry token is needed to download it.

The [publication run](https://github.com/DanielTea/generalgamebench/actions/runs/37271296373) ran all 50 `portable-v1` episodes and verified the completed submission archive separately on native AMD64 and ARM64 GitHub-hosted Linux machines. Both passed before their exact tested images were pushed. The [pre-merge run](https://github.com/DanielTea/generalgamebench/actions/runs/37271091573) also passed both architectures. CI evidence artifacts have limited retention; published image digests and these run records identify the distribution.

The unit suite passed 85 checks; 53 optional native-engine checks were skipped because those adapters did not change. Submission tests cover altered results and frames, incomplete suites, false trust claims, archive traversal, links, duplicate entries, upload-part corruption, missing parts, and resume behavior. Verification does not launch participant code.

Local validation on an Apple Silicon Mac used Docker Desktop's Linux ARM64 runtime. The portable control campaign completed 50 episodes and 3,586 decisions without errors or aborts, and passed exact native replay. A separate custom JSONL policy completed the ten-episode starter suite and its browser-upload parts verified successfully.

This validates the ten portable scenarios, not the entire 43-scenario extended installation. Native Windows transport and the Windows/WSL2 host path remain untested. Scores and latency measurements are local-unattested; the workflow is not an independent official ranking service.
