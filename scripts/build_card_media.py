"""Build card previews from published evidence, without calling any model.

Requires the v0.2.0 and v0.3.0 evidence archives at the repository root and ffmpeg.
Preview selection uses the longest random-control episode, then the lowest seed.
MiniWorld uses seed 4001, where the task's red box is visible in the recording.
Unity, Luanti and Cataclysm use their clear initial camera as the poster.
It never changes scores, episode selection, or the released result snapshot.
"""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from generalgamebench.evidence import verify_episode
from generalgamebench.games import DOOM

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site/dist"
RELEASE = "https://github.com/DanielTea/generalgamebench/releases/tag/v0.2.0"


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main():
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("Install ffmpeg before building media")
    catalog = json.loads((ROOT / "docs/catalog.json").read_text())
    sources = json.loads((SITE / "media/sources.json").read_text())
    roots = json.loads((ROOT / "results/season-0.2/evidence-roots.json").read_text())
    new_roots = json.loads((ROOT / "results/integrations-0.3/evidence-roots.json").read_text())
    roots.update(new_roots)
    for card in catalog:
        if card["status"] != "runnable":
            continue
        if card["id"] in ("coin-run", "dodge-lanes"):
            card["task_ids"] = [card["id"]]
        elif card["id"] == "vizdoom-eight-scenarios":
            card["task_ids"] = list(DOOM)
        task = card["task_ids"][0]
        candidates = []
        for relative in roots:
            path = Path(relative)
            if path.parent.name == "random" and path.name.startswith(task + "-"):
                frames = sorted((ROOT / path / "frames").glob("*.png"))
                candidates.append((path, frames))
        path, frames = sorted(candidates, key=lambda item: (-len(item[1]), str(item[0])))[0]
        if task == "miniworld-oneroom":
            path, frames = next(item for item in candidates if item[0].name.endswith("-4001"))
        poster_index = {
            "miniworld-oneroom": 19,
            "unity-food-collector": 0,
            "luanti-chop-tree": 0,
            "cdda-first-weapon": 0,
        }.get(task, len(frames) // 2)
        episode = ROOT / path
        verify_episode(episode, replay=False)
        head = json.loads((episode / "events.jsonl").read_text().splitlines()[-1])["hash"]
        if head != roots[str(path)]:
            raise ValueError(f"Episode is not the published evidence: {path}")
        release = RELEASE.replace("v0.2.0", "v0.3.0") if str(path) in new_roots else RELEASE
        frame_count = min(24, len(frames))
        image, video, animation = (f"media/{card['id']}.{ext}" for ext in ("webp", "mp4", "gif"))
        base = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
        subprocess.run(
            base
            + [
                "-i",
                str(frames[poster_index]),
                "-frames:v",
                "1",
                "-lossless",
                "1",
                str(SITE / image),
            ],
            check=True,
        )
        input_args = ["-framerate", "6", "-i", str(episode / "frames/%04d.png")]
        subprocess.run(
            base
            + input_args
            + [
                "-frames:v",
                str(frame_count),
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
            + input_args
            + [
                "-frames:v",
                str(frame_count),
                "-filter_complex",
                "[0:v]scale=384:-2:flags=neighbor,split[a][b];"
                "[a]palettegen[p];[b][p]paletteuse=dither=none",
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
            image_alt=f"{card['name']}: recorded {task} gameplay",
            media_kind="Recorded benchmark",
            media_source=release,
            preview_task=task,
            media_caption=f"Recorded {task} task with the random reference policy. "
            "Consecutive evaluation frames at 6 fps; playback speed does not measure reaction time.",
        )
        if card["id"] == "stable-retro-library":
            card["media_credit"] = "Airstriker demo authors / Stable-Retro contributors"
        source = next(s for s in sources if s["environment"] == card["name"])
        source.clear()
        source.update(
            environment=card["name"],
            image=image,
            video=video,
            animation=animation,
            source=release,
            source_page=release,
            credit=card["media_credit"],
            kind=card["media_kind"],
            episode=str(path),
            evidence_head=head,
            task=task,
            frames=frame_count,
            episode_frames=len(frames),
            poster_frame=poster_index,
            fps=6,
            sha256=hashlib.sha256((SITE / image).read_bytes()).hexdigest(),
            video_sha256=hashlib.sha256((SITE / video).read_bytes()).hexdigest(),
            animation_sha256=hashlib.sha256((SITE / animation).read_bytes()).hexdigest(),
        )
        print(f"{card['id']}: {len(frames)} verified frames", flush=True)
    save(ROOT / "docs/catalog.json", catalog)
    save(SITE / "media/sources.json", sources)
    # The website catalog may evolve independently of the immutable score release.
    snapshot = json.loads((SITE / "data.json").read_text())
    snapshot["catalog"] = catalog
    save(SITE / "data.json", snapshot)


if __name__ == "__main__":
    main()
