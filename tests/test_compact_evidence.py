import importlib.util
import io
import json
import tarfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, PngImagePlugin

SPEC = importlib.util.spec_from_file_location(
    "compact_evidence", Path(__file__).parents[1] / "scripts/compact_evidence.py"
)
codec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codec)


def evidence(tmp_path):
    frames = tmp_path / "runs/check/random/game-71/frames"
    frames.mkdir(parents=True)
    pixels = np.random.default_rng(71).integers(0, 256, (80, 120, 3), dtype=np.uint8)
    for i in range(4):
        pixels[0, i, 0] ^= 1
        pixels[0, 0, 0] = 0 if i % 2 else 255
        metadata = PngImagePlugin.PngInfo() if i == 2 else None
        if metadata is not None:
            metadata.add_text("example", "Preserve noncanonical PNG chunks verbatim")
        Image.fromarray(pixels).save(frames / f"{i:04d}.png", pnginfo=metadata)
    (frames.parent / "result.json").write_bytes(b'{"score": 0.0}\n')
    return sorted(p for p in (tmp_path / "runs").rglob("*") if p.is_file())


def rewrite(source, destination, change):
    with tarfile.open(source, "r:gz") as original, tarfile.open(destination, "w:gz") as edited:
        for record in original:
            payload = original.extractfile(record).read()
            record, payload = change(record, payload)
            record.size = len(payload)
            edited.addfile(record, io.BytesIO(payload))


def test_lossless_roundtrip_keeps_every_original_byte_and_encoder_fallback(tmp_path):
    files = evidence(tmp_path)
    first, second = tmp_path / "a.tar.gz", tmp_path / "b.tar.gz"
    result = codec.pack_files(files, tmp_path, first)
    codec.pack_files(files, tmp_path, second)
    assert first.read_bytes() == second.read_bytes()
    assert result["delta_frames"] == 2
    restored = tmp_path / "restored"
    assert codec.restore(first, restored)["original_checksums_verified"]
    for file in files:
        assert (restored / file.relative_to(tmp_path)).read_bytes() == file.read_bytes()


def test_payload_corruption_fails_checksum_verification(tmp_path):
    archive, corrupt = tmp_path / "a.tar.gz", tmp_path / "bad.tar.gz"
    codec.pack_files(evidence(tmp_path), tmp_path, archive)

    def change(record, payload):
        return record, (
            bytes([payload[0] ^ 1]) + payload[1:] if record.name.startswith("payload/") else payload
        )

    rewrite(archive, corrupt, change)
    with pytest.raises(ValueError, match="Corrupt evidence payload"):
        codec.restore(corrupt, tmp_path / "restored")


def test_rejects_path_traversal_without_writing_outside_destination(tmp_path):
    archive, corrupt = tmp_path / "a.tar.gz", tmp_path / "bad.tar.gz"
    codec.pack_files(evidence(tmp_path), tmp_path, archive)

    def change(record, payload):
        if record.name.startswith("payload/"):
            spec = json.loads(record.pax_headers["generalgamebench.record"])
            spec["path"] = "runs/../../escape"
            record.pax_headers["generalgamebench.record"] = json.dumps(spec)
        return record, payload

    rewrite(archive, corrupt, change)
    with pytest.raises(ValueError, match="Unsafe evidence path"):
        codec.restore(corrupt, tmp_path / "restored")
    assert not (tmp_path / "escape").exists()


def test_encoder_mismatch_is_rejected_before_restoring(tmp_path):
    archive, corrupt = tmp_path / "a.tar.gz", tmp_path / "bad.tar.gz"
    codec.pack_files(evidence(tmp_path), tmp_path, archive)

    def change(record, payload):
        if record.name == "manifest.json":
            manifest = json.loads(payload)
            manifest["encoder"]["zlib"] = "different-encoder"
            payload = json.dumps(manifest).encode()
        return record, payload

    rewrite(archive, corrupt, change)
    destination = tmp_path / "restored"
    with pytest.raises(ValueError, match="PNG encoder does not match"):
        codec.restore(corrupt, destination)
    assert not destination.exists()


def test_existing_destination_cannot_be_overwritten(tmp_path):
    with pytest.raises(FileExistsError):
        codec.restore(tmp_path / "unused.tar.gz", tmp_path)
