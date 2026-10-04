"""Lossless evidence transport: encode consecutive RGB differences, verify original PNG bytes.

The PNG encoder is recorded and must match when restoring. Unsupported PNGs and
all ledgers/results are stored verbatim. This never changes evaluation evidence.
"""

import argparse
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path, PurePosixPath

import numpy as np
from PIL import Image, __version__, features

FORMAT = "generalgamebench-evidence-delta/1"
MAX_MEMBER = 32 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[1]


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def encoder():
    return {"pillow": __version__, "zlib": features.version("zlib")}


def png(raw, size):
    output = io.BytesIO()
    Image.frombytes("RGB", size, raw).save(output, format="PNG")
    return output.getvalue()


def safe_path(name):
    path = PurePosixPath(name)
    if (
        not name
        or "\\" in name
        or ":" in name
        or path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != name
        or not path.parts
        or path.parts[0] != "runs"
    ):
        raise ValueError("Unsafe evidence path")
    return path


def pack_files(files, root, destination):
    if destination.exists():
        raise FileExistsError("Preserve prior artifacts; choose a new output")
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous, previous_path, previous_size = None, None, None
    original_bytes, delta_frames = 0, 0
    with destination.open("xb") as output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as archive:
                manifest = json.dumps(
                    {"format": FORMAT, "encoder": encoder(), "files": len(files)}
                ).encode()
                header = tarfile.TarInfo("manifest.json")
                header.size, header.mode = len(manifest), 0o644
                archive.addfile(header, io.BytesIO(manifest))
                for index, file in enumerate(files):
                    name = str(file.relative_to(root))
                    safe_path(name)
                    if file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
                        raise ValueError("Symlink or external evidence file")
                    original = file.read_bytes()
                    if len(original) > MAX_MEMBER:
                        raise ValueError("Evidence member exceeds the supported size")
                    original_bytes += len(original)
                    payload = original
                    spec = {
                        "path": name,
                        "sha256": sha(original),
                        "size": len(original),
                        "kind": "raw",
                    }
                    frame = None
                    if file.suffix == ".png":
                        with Image.open(io.BytesIO(original)) as image:
                            if image.mode == "RGB" and image.width * image.height * 3 <= MAX_MEMBER:
                                raw, size = image.tobytes(), image.size
                                pixels = np.frombuffer(raw, dtype=np.uint8)
                                frame = (pixels.copy(), name, size)
                                base = (
                                    previous_path
                                    if previous_size == size
                                    and previous_path
                                    and PurePosixPath(previous_path).parent
                                    == PurePosixPath(name).parent
                                    else None
                                )
                                # Canonical PNG bytes must be exactly reproducible.
                                if base is not None and png(raw, size) == original:
                                    residual = np.subtract(pixels, previous, dtype=np.uint8)
                                    encoded = png(residual.tobytes(), size)
                                    # Use original PNGs whenever the delta is not smaller.
                                    if len(encoded) < len(original):
                                        payload = encoded
                                        spec.update(
                                            kind="png-sub", width=size[0], height=size[1], base=base
                                        )
                                        delta_frames += 1
                    previous, previous_path, previous_size = frame or (None, None, None)
                    spec["payload_sha256"] = sha(payload)
                    record = tarfile.TarInfo(f"payload/{index:08d}")
                    record.size, record.mode, record.mtime = len(payload), 0o644, 0
                    record.pax_headers = {
                        "generalgamebench.record": json.dumps(spec, sort_keys=True)
                    }
                    archive.addfile(record, io.BytesIO(payload))
    return {
        "files": len(files),
        "delta_frames": delta_frames,
        "original_bytes": original_bytes,
        "archive_bytes": destination.stat().st_size,
    }


def restore(source, destination):
    if destination.exists():
        raise FileExistsError("Restore to a new directory; existing evidence is immutable")
    previous, previous_path, previous_size = None, None, None
    seen = set()
    with tarfile.open(source, "r|gz") as archive:
        first = archive.next()
        if (
            first is None
            or first.name != "manifest.json"
            or not first.isfile()
            or first.size > 4096
        ):
            raise ValueError("Invalid evidence manifest")
        manifest = json.loads(archive.extractfile(first).read())
        if manifest.get("format") != FORMAT or manifest.get("encoder") != encoder():
            raise ValueError(
                "Use the pinned evidence-codec Docker image; PNG encoder does not match"
            )
        count = manifest.get("files")
        if type(count) is not int or not 0 <= count <= 100000:
            raise ValueError("Invalid evidence file count")
        destination.mkdir(parents=True)
        for index in range(count):
            record = archive.next()
            if (
                record is None
                or record.name != f"payload/{index:08d}"
                or not record.isfile()
                or record.size > MAX_MEMBER
            ):
                raise ValueError("Invalid evidence member")
            spec = json.loads(record.pax_headers["generalgamebench.record"])
            path = safe_path(spec["path"])
            if str(path) in seen:
                raise ValueError("Duplicate evidence path")
            seen.add(str(path))
            payload = archive.extractfile(record).read()
            if sha(payload) != spec["payload_sha256"]:
                raise ValueError("Corrupt evidence payload")
            if spec["kind"] == "png-sub":
                width, height = spec["width"], spec["height"]
                if (
                    type(width) is not int
                    or type(height) is not int
                    or width <= 0
                    or height <= 0
                    or width * height * 3 > MAX_MEMBER
                ):
                    raise ValueError("Invalid RGB dimensions")
                size = (width, height)
                base = spec.get("base")
                if (
                    previous is None
                    or base != previous_path
                    or size != previous_size
                    or PurePosixPath(base).parent != path.parent
                ):
                    raise ValueError("Invalid delta base")
                with Image.open(io.BytesIO(payload)) as residual:
                    if residual.mode != "RGB" or residual.size != size:
                        raise ValueError("Invalid residual image")
                    pixels = np.add(
                        np.frombuffer(residual.tobytes(), dtype=np.uint8), previous, dtype=np.uint8
                    )
                original = png(pixels.tobytes(), size)
                previous, previous_path, previous_size = pixels.copy(), str(path), size
            elif spec["kind"] == "raw":
                original = payload
                previous, previous_path, previous_size = None, None, None
            else:
                raise ValueError("Unknown evidence encoding")
            if len(original) != spec["size"] or sha(original) != spec["sha256"]:
                raise ValueError("Original file checksum mismatch")
            if spec["kind"] == "raw" and path.suffix == ".png":
                with Image.open(io.BytesIO(original)) as frame:
                    if frame.mode == "RGB" and frame.width * frame.height * 3 <= MAX_MEMBER:
                        previous, previous_path, previous_size = (
                            np.frombuffer(frame.tobytes(), dtype=np.uint8).copy(),
                            str(path),
                            frame.size,
                        )
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original)
        if archive.next() is not None:
            raise ValueError("Unexpected trailing evidence member")
    return {"files": len(seen), "original_checksums_verified": True}


def selected_files(selection):
    from generalgamebench.evidence import verify_episode

    roots = json.loads(selection.read_text())
    files = []
    for relative, expected in sorted(roots.items()):
        safe_path(relative)
        episode = ROOT / relative
        verify_episode(episode, replay=False)
        if json.loads((episode / "events.jsonl").read_text().splitlines()[-1])["hash"] != expected:
            raise ValueError("Evidence selection root changed")
        for file in sorted(episode.rglob("*")):
            if file.is_symlink():
                raise ValueError("Symlink in evidence")
            if not file.is_file():
                continue
            relative_file = file.relative_to(episode)
            if str(relative_file) not in {"events.jsonl", "result.json"} and not (
                relative_file.parent == Path("frames") and file.suffix == ".png"
            ):
                raise ValueError("Unexpected evidence file")
            files.append(file)
    return files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    packing = commands.add_parser("pack")
    packing.add_argument("--selection", type=Path, required=True)
    packing.add_argument("--output", type=Path, required=True)
    unpacking = commands.add_parser("restore")
    unpacking.add_argument("archive", type=Path)
    unpacking.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            pack_files(selected_files(args.selection), ROOT, args.output)
            if args.command == "pack"
            else restore(args.archive, args.destination)
        )
    )
