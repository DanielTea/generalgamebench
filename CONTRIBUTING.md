# Contributing

Run `uv sync --extra doom --extra dev`, then `uv run pytest`, `uv run ruff check .` and `uv run ruff format --check .` before proposing a change. Python 3.12 is the reference runtime. Use small focused pull requests and include the task/version and relevant replay evidence.

Game adapters need documented asset rights, reset/seed semantics, rendered observations, allowed controls, native scoring, fixed normalization bounds, termination and a deterministic replay test. Commercial game files and model weights must not be committed. Never claim a researched candidate is integrated.

Agent submissions use the issue form. State model/version, policy hash, hardware, external services, training/test separation and all run failures. Public development results remain provisional. Do not ask reviewers to execute untrusted code on their workstation.

Timing or scoring changes require a version/season bump and new results. Formatting, documentation and semantic validation improvements that do not change observations, controls or scoring do not authorize silently rerunning only bad seeds. Preserve all final-campaign trials.

Be respectful, provide reproducible reports, and distinguish observations from claims. Original contributions are under the repository's MIT license; third-party material keeps its existing license.
