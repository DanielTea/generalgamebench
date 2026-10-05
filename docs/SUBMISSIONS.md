# Run and submit a benchmark

The portable runner includes **ten scenarios**: two bundled 2D games and eight ViZDoom scenarios. It needs Docker, Git and a shell; no local Python, game accounts or model API keys are needed for the example policy. The image supports Linux AMD64 and ARM64. Use Docker Desktop on macOS, Docker on Linux, or a WSL2 shell with Docker on Windows. Windows/WSL2 host operation has not yet been independently tested.

## 1. Run the example

Start Docker, then:

```sh
git clone https://github.com/DanielTea/generalgamebench.git
cd generalgamebench
./ggbench
```

The launcher downloads the pinned image, selects the native processor architecture, runs all 50 fixed episodes, independently replays their native frames and scores, and packages the results. It uses the bundled `react` control policy. No hosted model is called and nothing is uploaded automatically. The image reference lives in `environments/portable/image.txt`; the actual immutable image ID and source fingerprint are recorded in the submission.

Results appear in `runs/submission/`:

- `SUBMIT.txt`: a prefilled GitHub review link and upload instructions.
- `uploads/`: ZIP parts small enough to attach to a GitHub issue. Attach **every part**.
- `submission.zip`: the complete evidence archive, useful for independent download hosting.
- `submission/report.md`: a readable score and latency report.
- `submission/submission.json`: versioned metadata and computed ranking.
- `submission/episodes/`: every episode, including agent timeouts and failures, with native screenshots and hash-linked action/timing records.
- `SHA256SUMS`: checksums of the archive and its upload parts.

Do not compare the example against the website's older 33-task cohort. Suite, evaluator, game runtimes, hardware, mode and horizon must match for a direct comparison. Timing on different CPUs or under emulation is not interchangeable.

## 2. Connect your agent

Your program uses the [JSON-lines protocol](PROTOCOL.md): print `{"ready":true}`, read a PNG observation and allowed actions, then return its nonce and an integer action. Logs go to stderr. [examples/agent.py](../examples/agent.py) is a runnable starting point.

By default, `examples/` is mounted read-only at `/agent`. For your own policy folder:

```sh
GGBENCH_AGENT_DIR=/absolute/path/to/my-agent ./ggbench benchmark \
  --agent-command 'python /agent/agent.py' \
  --name my-agent \
  --agent-revision 'REPLACE_WITH_IMMUTABLE_SOURCE_OR_MODEL_REVISION' \
  --hardware 'REPLACE_WITH_CPU_GPU_AND_MEMORY' \
  --output /results/my-agent
```

Use `/results/...` for container outputs; these map to the repository's `runs/` folder. The command and policy identity must stay unchanged through the campaign. The archive includes referee data only, not your code, model weights, environment files or credentials. Link public source and model revisions in the submission form so reviewers can reproduce the policy.

For extra policy dependencies, derive your own image from the pinned runner and select it with `GGBENCH_IMAGE=your-image`. Keep its digest and dependency lockfile. The default container has no network; policies that require their own network service can explicitly set `GGBENCH_NETWORK=bridge`. Network response time is inside the measured decision path. Configure credentials in your own policy setup, outside the repository and public evidence. Provider-specific local CLIs can instead use the native Python workflow below.

Only run agents you trust. The local runner and Docker launcher are development tools; neither makes participant-controlled evidence independently authenticated.

## 3. Submit for review

Open the link in `SUBMIT.txt`, drag every ZIP from `uploads/` into the evidence field, and describe your agent revision, hardware, training overlap and external services. A GitHub account is needed to open the issue; repository write access is not needed.

Files are split into 20 MiB payloads because GitHub's [ZIP attachment limit is 25 MB](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files). For a large extended-suite run, you may instead host `submission.zip` in a public release and link its checksum. The verifier accepts either form.

Submissions enter **community review**, not automatic official ranking. Reviewers check completeness, image hashes, native replay and calculated scores without executing your policy. Independent timing, hidden-seed evaluation and official attestation remain separate infrastructure.

## Verify evidence

Put a downloaded full archive under `runs/downloaded/`:

```sh
./ggbench verify-submission /results/downloaded/submission.zip
```

Or put **all** upload parts together in that directory:

```sh
./ggbench verify-submission /results/downloaded
```

Use the evaluator release and pinned image recorded in the submission. Verification does not fetch an image or execute a policy named inside an archive. Unsafe paths, links, duplicate members, oversized payloads, missing parts, altered evidence, incomplete suites and forged rankings fail validation. Archives are limited to 8 GiB uncompressed, 100,000 files and 32 MiB per member. `--no-replay` checks internal integrity only; it does not confirm native gameplay scores or authenticate timing.

## Suites and modes

| Suite | Scenarios | Episodes | Purpose |
| --- | ---: | ---: | --- |
| `starter-v1` | 2 | 10 | Quick policy integration check |
| `portable-v1` | 10 | 50 | Default Docker submission |
| `extended-v1` | 43 | 215 | All admitted tasks, after separate runtime installation |

Each suite uses seeds 1000–1004 and at most 80 decisions per episode, respecting native terminal states. Suite definitions and task revisions are fingerprinted. These community suites are separate from historical leaderboard cohorts.

The default **exhibition** mode includes slower agents and publishes measured latency. Add `--mode realtime` for the strict deadline track. Every measured decision must be **strictly below 100 ms** for latency eligibility. Five development seeds are an accessible starting cohort, not strong evidence of broad generalization.

```sh
./ggbench doctor
./ggbench suites
./ggbench benchmark --suite starter-v1 --output /results/quick-check
./ggbench benchmark --mode realtime --output /results/realtime
```

`--resume` reuses completed episodes only when configuration, evaluator, environment and policy identity still match. It repairs missing upload parts without calling the agent again. It refuses partial episodes instead of silently discarding interrupted trials. Preserve such a campaign, start a new output and disclose the interruption. Existing outputs are never silently overwritten.

## Full suite and native installation

The portable image does **not** contain all 43 scenarios or commercial games. Nine additional engines use separately built Linux ARM64 containers; other tasks have isolated Python environments, and Unity uses a Mac executable. See [runtime installation and platform limits](../environments/README.md).

```sh
uv sync --frozen --extra doom
uv run generalgamebench doctor --suite extended-v1
# Follow the reported runtime installation instructions.
uv run generalgamebench benchmark --suite extended-v1 --output runs/extended
```

The benchmark refuses missing runtimes instead of silently reducing coverage. Native Windows referee pipes remain unsupported; use Docker or Linux there.

## Rebuild the image

```sh
docker build -f environments/portable/Dockerfile -t ggbench-portable:local .
GGBENCH_IMAGE=ggbench-portable:local ./ggbench
```

Base images and Python dependencies are pinned. Distribution package mirrors can change, so source rebuilding does not guarantee an identical image; use the published digest for an exact runtime. The [portable workflow](../.github/workflows/portable.yml) runs the full portable suite and verifies its archive on native AMD64 and ARM64 Linux runners before publishing. It runs only repository-owned policies, never submitted agent code.

The `generalgamebench-submission/1` format is independent of the website host. Its suite identity, provenance, evidence and trust labels can be reused by a future Hugging Face intake service; the static Space remains a display layer.
