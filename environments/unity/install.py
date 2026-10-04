"""Download the official pinned Mac example, verify it, and extract locally."""

import hashlib
import json
import shutil
import stat
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    manifest = json.loads(Path(__file__).with_name("assets.json").read_text())
    destination = ROOT / ".game-assets/unity"
    if destination.exists():
        raise FileExistsError(
            "Unity assets already exist; preserve them and inspect before reinstalling"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        folder = Path(temporary)
        archive = folder / "Startup.zip"
        with (
            urllib.request.urlopen(manifest["url"], timeout=120) as response,
            archive.open("wb") as file,
        ):
            shutil.copyfileobj(response, file)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["archive_sha256"]:
            raise ValueError("Unity archive checksum mismatch")
        with zipfile.ZipFile(archive) as zipped:
            for item in zipped.infolist():
                target = (folder / item.filename).resolve()
                if not target.is_relative_to(folder.resolve()):
                    raise ValueError("Unsafe archive path")
                if stat.S_ISLNK(item.external_attr >> 16):
                    raise ValueError("Unexpected archive symlink")
            zipped.extractall(folder)
        executable = folder / manifest["application"] / "Contents/MacOS/UnityEnvironment"
        executable.chmod(0o755)
        folder.rename(destination)
    print("Pinned Unity example installed. See environments/README.md for verification.")


if __name__ == "__main__":
    main()
