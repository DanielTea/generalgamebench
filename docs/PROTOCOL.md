# Participant protocol v1

Your program reads UTF-8 JSONL on stdin and writes UTF-8 JSONL on stdout. Logs go to stderr. Flush every line. Before receiving observations, print exactly `{"ready":true}`; process startup has a 10-second limit. Warm model/image codecs before this readiness signal.

Observation:

```json
{"protocol":"screenquest/1","nonce":"opaque-new-challenge","image_png":"base64 PNG","actions":["wait","left","right","up","down"],"instructions":"Public game rules"}
```

Response (no other fields):

```json
{"nonce":"opaque-new-challenge","action":2}
```

Action is a true JSON integer in `[0, len(actions))`; booleans and floats are rejected. A response must be <=4096 bytes. One outstanding observation, one reply. Guessed/stale nonces, extra fields, oversized lines, broken pipes and malformed JSON invalidate the episode. Never include a self-reported score or timestamp. Seeds and referee state are absent from observations.

`--agent-command` is parsed into arguments and executed without a shell. It still executes a program with local user privileges: only use trusted local policies. The example container launcher uses no network, readonly root, resource limits and an unprivileged user; this is a deployment starting point, not certified isolation.

## Integrating a game

A trusted game adapter provides `id`, `actions`, `instructions`, `done`, `frame()->PNG bytes`, `step(integer)`, `result()->{raw_score, score, steps, metrics}` and `close()`. It runs with the referee, never in the participant process. Use `games.py` as the small reference and add deterministic fixtures before adding it to a season.

For desktop games, implement dedicated capture and bounded input on a licensed evaluation host, native replay/save resets and independent outcome measurement. Do not expose game memory, hidden minimap entities, DOM state or privileged scripting to a pixels-only agent. An engine-specific referee may read state to score, as long as that channel cannot reach the participant.

## Submission

The [run-and-submit guide](SUBMISSIONS.md) provides a Docker launcher, fixed suites, automatic replay and upload-ready evidence. Use `benchmark` for a complete campaign and `verify-submission` for a full archive or its upload parts. The versioned `generalgamebench-submission/1` format records suite identity, policy revision, evaluator fingerprint, runtime, evidence roots and calculated rankings without embedding policy code or credentials.

1. Run the same declared suite locally.
2. Verify every episode and retain all attempted trials.
3. Open the repository's **Agent evaluation submission** issue with source/model hashes, exact environment, full results and downloadable evidence. Never attach credentials, browser profiles or proprietary game assets.
4. Maintainers inspect the artifacts and reproduce runs. No issue or uploaded score grants an official rank. Until independent infrastructure is deployed, results stay provisional.

The `screenquest/1` protocol identifier is retained from the initial release for compatibility. GeneralGameBench is the current project name.
