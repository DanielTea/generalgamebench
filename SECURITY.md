# Security and benchmark integrity

**No claim of an uncheatable system.** The current local runner is not safe for arbitrary hostile executables. It is for trusted participant development and transparent baseline experiments. The official track remains empty.

## Implemented controls

- The referee owns seeded game state, scores, monotonic timestamps and action application.
- Participants receive PNG observations, public rules, allowed actions and a fresh 128-bit nonce. No seeds, game coordinates, memory, reward or judge APIs enter the protocol.
- Actions must match the current nonce and strict schema. Size limits, deadlines, nonblocking writes and process-group termination prevent common protocol stalls.
- Environment variables are allowlisted for ordinary process agents; provider credentials are not handed to them.
- Late/invalid actions do not receive useful controls; transport failures abort and score zero.
- Evidence is hash-linked, and replay recomputes frames and scores. Final timing/score summaries are checked against step evidence.
- The static website cannot execute agents or accept authoritative scores. Submissions are reviewed through GitHub. Pull-request CI runs repository tests without deployment secrets; never use pull_request_target to run participant code.

## What these controls do not prevent

A local process under the same user can read referee files, inspect processes or tamper with storage. It may know public development seeds. A local operator can rewrite an entire ledger and all timestamps. Hash chains and successful replay do not authenticate the machine or prove genuine timing. A container alone shares a kernel and is not a complete adversarial security boundary. Model CLIs use local account authentication and are suitable only for this explicitly labeled trusted exhibition.

## Production boundary required for official ranks

1. Independent runner operated by the leaderboard, with a separate VM/microVM per submission, patched host, minimal syscall/device exposure, CPU/GPU/memory/process/time quotas and pinned image digests.
2. Referee/game in a different trust domain; agent sees only a bounded observation/action relay. No shared filesystem, host PID namespace, game process, Docker socket, cloud metadata or scoring endpoint.
3. Default-deny egress. A provider broker may allow approved model calls with per-run credentials, request budgets and complete measured transit. Remote-model and local-model hardware divisions remain explicit.
4. Server-selected hidden seeds after immutable submission freeze. Reused, leaked or contaminated seeds require a new season, not selective re-scoring.
5. Runner signature over manifest, image/model/code digests, complete evidence root and timing policy. Signing keys live outside participant/worker containers; ingestion trusts only administrator-approved keys.
6. Independent replay/adjudication, provenance retention, adversarial testing, rate limits, removal/appeal procedure and incident response.

The portable `ggbench` launcher uses a read-only root, the invoking user’s UID, dropped capabilities, bounded processes and no network by default. Game execution is tested in Docker, but the local referee and policy still share a trust domain. This is not an adversarial worker service. The separate sample `scripts/container-agent.py` remains a development wrapper, not certified isolation.

The `verify-submission` command treats archives as data. It bounds decompressed sizes and file counts, rejects unsafe paths, duplicate members and links, checks full suite membership and recalculates rankings. Native replay runs only installed repository-owned game adapters; it never executes submitted policy code or pulls an image named by the submission. Upload parts have per-part and full-archive checksums. Successful validation retains `local-unattested` trust and cannot authenticate participant timing or confer an official rank.

Report vulnerabilities through the repository's private vulnerability reporting feature if enabled. Do not publish credentials, exploitation payloads against live users, or private evaluation seeds in public issues.
