"""Package only the replay-verified public episode selection, deterministically."""

import argparse
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def package(selection: Path, destination: Path):
    if destination.exists():
        raise FileExistsError("Preserve prior release artifacts; choose a new path")
    roots = json.loads(selection.read_text())
    files = []
    for relative, expected_head in sorted(roots.items()):
        episode = ROOT / relative
        if not episode.resolve().is_relative_to(ROOT / "runs") or episode.is_symlink():
            raise ValueError("Evidence selection must contain local run directories")
        head = json.loads((episode / "events.jsonl").read_text().splitlines()[-1])["hash"]
        if head != expected_head:
            raise ValueError(f"Evidence root changed: {relative}")
        for file in sorted(episode.rglob("*")):
            if file.is_symlink():
                raise ValueError("Symlinks do not belong in public evidence")
            if not file.is_file():
                continue
            name = file.relative_to(episode)
            if name.as_posix() not in {"events.jsonl", "result.json"} and not (
                name.parent == Path("frames") and name.suffix == ".png"
            ):
                raise ValueError(f"Unexpected public evidence file: {name}")
            files.append(file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|") as archive:
                for file in files:
                    payload = file.read_bytes()
                    record = tarfile.TarInfo(file.relative_to(ROOT).as_posix())
                    record.size, record.mode, record.mtime = len(payload), 0o644, 0
                    archive.addfile(record, io.BytesIO(payload))
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {"episodes": len(roots), "files": len(files), "sha256": digest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--selection", type=Path, default=Path("results/season-0.2/evidence-roots.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.selection, args.output)))
