# Full suite on Linux

Use Linux x86_64 for the full 43-scenario suite. Ubuntu 24.04 is the test platform.
The referee and the model run on the same host. Nine game engines use separate
Docker images. The other engines use separate Python environments.

Install Git, Docker Engine, and uv 0.9.26. Start Docker. Give the current user access
to the Docker daemon. Then run these commands from the repository root:

```sh
uv sync --frozen --python 3.12 --extra doom --extra dev --extra hub
sudo apt-get update
sudo apt-get install -y $(uv run --no-sync python scripts/install_linux.py --system-packages)
uv run --no-sync python scripts/install_linux.py
uv run --no-sync generalgamebench doctor --suite extended-v1
uv run --no-sync generalgamebench benchmark --suite extended-v1 --output runs/linux-full
```

The installer selects AMD64 game images on Linux x86_64. It retains the pinned
engine revisions, patches, and assets. Set `GGBENCH_BUILD_JOBS` to change the number
of compiler workers. The default is two.

Unity uses the official ML-Agents 1.1.0 Linux executable. Its archive and extracted
files have separate SHA-256 checksums. No Mac executable or Unity Editor is needed.
Unity, MiniWorld, and Airstriker use a private Xvfb display on Linux. The model still
receives the native RGB game image.

The existing Mac installation uses its original ARM64 engine images and Mac Unity
assets. These images have different identities from the Linux AMD64 images.
Compare scores only when the suite, engine metadata, hardware, and test settings
match. A matching seed does not guarantee matching pixels across platforms.

The full suite requires Linux x86_64 because the pinned Unity and Procgen binaries
use that processor architecture. The ten-scenario portable image also supports
Linux ARM64.

## Validation

The `Full Linux suite` workflow installs each runtime on native Ubuntu x86_64.
It records and independently replays all 43 scenarios. Each replay checks every
PNG frame, action, native result, and normalized score. The final job rejects
missing scenarios, duplicate scenarios, and reports from a different commit.

The workflow retains the screenshots and action records as downloadable artifacts.
A successful installation check alone does not establish replay correctness.
