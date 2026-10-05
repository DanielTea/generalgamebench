"""Install the pinned Unity example for the current operating system."""

import hashlib
import shutil
import stat
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from generalgamebench.unity_engine import asset_digest, unity_manifest

ROOT = Path(__file__).resolve().parents[2]


def main():
    manifest = unity_manifest()
    destination = ROOT / manifest.get("install_directory", ".game-assets/unity")
    if destination.exists():
        if asset_digest(destination / manifest["application"]) != manifest["app_tree_sha256"]:
            raise ValueError("Existing Unity assets differ. Inspect them before reinstalling.")
        print("Pinned Unity assets are already installed.")
        return
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
        executable = (
            folder
            / manifest["application"]
            / manifest.get("executable", "Contents/MacOS/UnityEnvironment")
        )
        executable.chmod(0o755)
        if asset_digest(folder / manifest["application"]) != manifest["app_tree_sha256"]:
            raise ValueError("Extracted Unity assets differ from the pinned input tree.")
        folder.rename(destination)
    print("Pinned Unity example installed. See environments/README.md for verification.")


if __name__ == "__main__":
    main()
