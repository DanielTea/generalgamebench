# Portable runner 0.5.0

The default image is pinned in `image.txt`:

```text
ghcr.io/danieltea/generalgamebench@sha256:9cceac2129ea970b45b76aa63b1f554097bbbe7ac25305425f6a1dbe4d5a4a69
```

The image contains native Linux AMD64 and ARM64 builds.
Both builds use source revision `ae95579a99d8b8362114ac933e7f5ce6bf0c238e`.
Both passed all 50 portable episodes and separate submission replay before publication.
The [publication run](https://github.com/DanielTea/generalgamebench/actions/runs/37300621975) identifies the tested builds.
The [pull request check](https://github.com/DanielTea/generalgamebench/actions/runs/37300271471) also passed on both architectures.

The leaderboard limit is **suite p95 below 200 ms**. Exactly 200 ms fails.
The calculation pools all recorded response times. It uses linear interpolation.
A valid response above 200 ms stays in the test until the configured transport timeout.
The default timeout is 60 seconds. A timeout aborts the episode with score zero.
Scores, errors and trust status stay separate from the latency test.

Anonymous registry requests retrieved the index and both platform manifests on 5 October 2026.
Their content hashes match the published digests.
No registry login is needed to download this image.

The image contains the ten portable scenarios.
The full 43-scenario suite needs additional runtimes.
Local results remain `local-unattested`. A latency pass does not grant an official rank.

---

The following record describes the previous image. Its evidence remains unchanged.

# Historical portable runner 0.4.0

The published multi-architecture image is pinned in `image.txt`:

```text
ghcr.io/danieltea/generalgamebench@sha256:1fabc2750c87ba08f4429715b2e7a07b36c20464d554744eba1164d9bda4eb2a
```

It contains Linux AMD64 and Linux ARM64 images built from source revision `9a22a0af1a56ce4f09284b760ba99adec0376e1f`. An unauthenticated registry request successfully retrieved both platform manifests on 2026-10-05. No GitHub login or registry token is needed to download it.

The [publication run](https://github.com/DanielTea/generalgamebench/actions/runs/37271296373) ran all 50 `portable-v1` episodes and verified the completed submission archive separately on native AMD64 and ARM64 GitHub-hosted Linux machines. Both passed before their exact tested images were pushed. The [pre-merge run](https://github.com/DanielTea/generalgamebench/actions/runs/37271091573) also passed both architectures. CI evidence artifacts have limited retention; published image digests and these run records identify the distribution.

The unit suite passed 85 checks; 53 optional native-engine checks were skipped because those adapters did not change. Submission tests cover altered results and frames, incomplete suites, false trust claims, archive traversal, links, duplicate entries, upload-part corruption, missing parts, and resume behavior. Verification does not launch participant code.

Local validation on an Apple Silicon Mac used Docker Desktop's Linux ARM64 runtime. The portable control campaign completed 50 episodes and 3,586 decisions without errors or aborts, and passed exact native replay. A separate custom JSONL policy completed the ten-episode starter suite and its browser-upload parts verified successfully.

This validates the ten portable scenarios, not the entire 43-scenario extended installation. Native Windows transport and the Windows/WSL2 host path remain untested. Scores and latency measurements are local-unattested; the workflow is not an independent official ranking service.
