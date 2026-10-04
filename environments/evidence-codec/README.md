# Lossless evidence transport

The v0.3 evidence release uses `generalgamebench-evidence-v0.3.0.delta.tar.gz`. This is a compact transport archive, not an ordinary directory of PNGs. It preserves every original ledger, result and PNG byte, including the PNG encoding. The independent replay checks were performed before packing; packing cannot change scores or timing.

Consecutive RGB images can be stored as PNG-compressed byte differences modulo 256. The smaller of that representation and the original PNG is retained. Images with extra metadata or a different PNG encoding remain verbatim. Every payload and reconstructed original file has a SHA-256 check. Original episode paths remain unchanged after restoration.

## Restore the public evidence

Check the download against the release's `SHA256SUMS`. From the repository root, with the downloaded archive in `build/releases/v0.3.0/`:

```sh
docker build --platform linux/arm64 -t ggbench-evidence-codec:1 environments/evidence-codec
mkdir -p build/restored
docker run --rm --network none --read-only --tmpfs /tmp \
  --mount type=bind,src="$PWD/scripts",dst=/codec,readonly \
  --mount type=bind,src="$PWD/build/releases/v0.3.0",dst=/archive,readonly \
  --mount type=bind,src="$PWD/build/restored",dst=/output \
  ggbench-evidence-codec:1 restore \
  /archive/generalgamebench-evidence-v0.3.0.delta.tar.gz /output/evidence
uv run generalgamebench verify \
  build/restored/evidence/runs/integration-release-0.3-verified/random/warzone-first-derrick-5000
```

Game replay additionally requires that game's pinned runtime. Restoring and inspecting PNGs needs no game engine or provider credentials. The destination must not exist; failed restoration leaves its partial output for inspection. To use the card-media builder, keep the restored episode directories at their recorded paths under the repository's `runs/` directory.

The reference encoder uses Linux ARM64, Pillow 11.3.0 and zlib 1.3.1. A Mac Pillow wheel can use zlib-ng and produce different PNG bytes, even at the same Pillow version. The decoder therefore requires the recorded encoder identity and checks every original checksum before writing the file. Use the pinned Docker recipe instead of changing that check.

`scripts/compact_evidence.py pack --selection results/integrations-0.3/evidence-roots.json --output <new archive>` creates the format with the same encoder. It verifies each selected episode's ledger/frame hashes before packing. The older `scripts/package_evidence.py` remains available for ordinary full-PNG archives. Neither transport changes the evidence or replaces independent replay.
