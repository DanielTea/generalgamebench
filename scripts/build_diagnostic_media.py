"""Build explicitly unranked candidate previews from released native captures.

Extract generalgamebench-diagnostic-media-v0.3.0.tar.gz at the repo root first.
These captures have failed replay admission and must never become score evidence.
"""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site/dist"


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main():
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("Install ffmpeg before building media")
    manifest = json.loads((ROOT / "results/integrations-0.3/diagnostic-media.json").read_text())
    catalog = json.loads((ROOT / "docs/catalog.json").read_text())
    sources = json.loads((SITE / "media/sources.json").read_text())
    for spec in manifest:
        card = next(c for c in catalog if c["id"] == spec["card"])
        if card["status"] == "runnable":
            raise ValueError("Diagnostic media must not replace admitted task evidence")
        directory = ROOT / spec["directory"]
        for name, digest in spec["frame_sha256"].items():
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f"Diagnostic frame changed: {name}")
        image, video, animation = (f"media/{card['id']}.{ext}" for ext in ("webp", "mp4", "gif"))
        base = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
        subprocess.run(
            base
            + [
                "-i",
                str(directory / spec["poster"]),
                "-frames:v",
                "1",
                "-lossless",
                "1",
                str(SITE / image),
            ],
            check=True,
        )
        inputs = [
            "-framerate",
            "6",
            "-i",
            str(directory / "%04d.png"),
            "-frames:v",
            str(len(spec["frame_sha256"])),
        ]
        subprocess.run(
            base
            + inputs
            + [
                "-vf",
                "scale=512:-2:flags=neighbor",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-an",
                str(SITE / video),
            ],
            check=True,
        )
        subprocess.run(
            base
            + inputs
            + [
                "-filter_complex",
                "[0:v]scale=384:-2:flags=neighbor,split[a][b];[a]palettegen[p];[b][p]paletteuse=dither=none",
                "-loop",
                "0",
                str(SITE / animation),
            ],
            check=True,
        )
        card.update(
            image=image,
            video=video,
            animation=animation,
            image_alt=f"{card['name']}: native diagnostic capture, unranked",
            media_kind="Native diagnostic · unranked",
            media_source=spec["source"],
            media_credit=spec["credit"],
            media_caption="Native prototype capture. Exact visual replay failed; this candidate has no admitted task or ranking. Consecutive frames at 6 fps do not measure reaction time.",
        )
        source = next(s for s in sources if s["environment"] == card["name"])
        source.clear()
        source.update(
            environment=card["name"],
            image=image,
            video=video,
            animation=animation,
            source=spec["source"],
            source_page=spec["source"],
            credit=spec["credit"],
            kind=card["media_kind"],
            diagnostic_manifest="results/integrations-0.3/diagnostic-media.json",
            frames=len(spec["frame_sha256"]),
            fps=6,
            poster_frame=int(Path(spec["poster"]).stem),
            sha256=hashlib.sha256((SITE / image).read_bytes()).hexdigest(),
            video_sha256=hashlib.sha256((SITE / video).read_bytes()).hexdigest(),
            animation_sha256=hashlib.sha256((SITE / animation).read_bytes()).hexdigest(),
        )
        print(f"{card['name']}: {len(spec['frame_sha256'])} unranked diagnostic frames", flush=True)
    save(ROOT / "docs/catalog.json", catalog)
    save(SITE / "media/sources.json", sources)
    snapshot = json.loads((SITE / "data.json").read_text())
    snapshot["catalog"] = catalog
    save(SITE / "data.json", snapshot)


if __name__ == "__main__":
    main()
