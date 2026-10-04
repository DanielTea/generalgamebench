"""Verify the installed OpenGFX inputs during the image build."""

import hashlib
import json
from pathlib import Path

folder = Path("/source/build/baseset/opengfx")
expected = json.loads(Path("/source/assets-hashes.json").read_text())
actual = {
    p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()
}
if actual != expected:
    raise ValueError("OpenGFX assets differ from the validated snapshot")
