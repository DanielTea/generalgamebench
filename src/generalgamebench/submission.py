"""Reproducible local campaigns and bounded, data-only submission archives.

Verification never executes submitted agent code. Local evidence, including its
hardware and timing claims, remains unauthenticated after successful replay.
"""

import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shlex
import stat
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path, PurePosixPath
from urllib.parse import urlencode

from . import __version__
from .evidence import canonical, digest, read_ledger, verify_episode
from .protocol import ProcessAgent
from .ranking import summarize
from .runner import run_episode
from .suites import SUITES

FORMAT = "generalgamebench-submission/1"
MAX_FILES = 100_000
MAX_MEMBER = 32 * 1024 * 1024
MAX_TOTAL = 8 * 1024**3
MAX_MANIFEST = 8 * 1024 * 1024
UPLOAD_CHUNK = 20 * 1024 * 1024
PART_FORMAT = "generalgamebench-upload-part/1"
ISSUE_URL = "https://github.com/DanielTea/generalgamebench/issues/new"


def file_sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def environment():
    packages = {}
    for name in ("numpy", "Pillow", "vizdoom"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    source = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        source.update(path.name.encode() + b"\0" + path.read_bytes())
    return {
        "evaluator_version": __version__,
        "evaluator_sha256": source.hexdigest(),
        "python": platform.python_version(),
        "system": platform.system(),
        "architecture": platform.machine(),
        "packages": packages,
        "zlib": zlib.ZLIB_RUNTIME_VERSION,
        "image_revision": os.environ.get("GGBENCH_IMAGE_REVISION", "not-containerized"),
        "image_reference": os.environ.get("GGBENCH_IMAGE_REFERENCE", "not-recorded"),
        "image_id": os.environ.get("GGBENCH_IMAGE_ID", "not-recorded"),
    }


def _read_json(path, limit=MAX_MANIFEST):
    if path.is_symlink() or path.stat().st_size > limit:
        raise ValueError(f"Oversized JSON or symlink: {path.name}")
    return json.loads(path.read_text())


def _write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def _episode_files(root):
    """Allow only referee data; never sweep agent source or credentials into ZIPs."""
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlinks are not allowed in submission evidence")
        if path.is_dir():
            continue
        relative = path.relative_to(root).as_posix()
        if not re.fullmatch(r"(?:events\.jsonl|result\.json|frames/[0-9]{4,}\.png)", relative):
            raise ValueError(f"Unexpected evidence file: {relative}")
        if not path.is_file() or path.stat().st_size > MAX_MEMBER:
            raise ValueError("Invalid or oversized evidence file")
        files.append(path)
    return files


def _validate_directory(root, replay):
    manifest = _read_json(root / "submission.json")
    if manifest.get("format") != FORMAT or manifest.get("trust") != "local-unattested":
        raise ValueError("Unknown submission format or invalid trust claim")
    suite_id = manifest.get("suite", {}).get("id")
    if suite_id not in SUITES:
        raise ValueError("Unknown suite; use the matching benchmark release")
    suite = SUITES[suite_id]
    if manifest["suite"] != suite.definition() or manifest.get("suite_sha256") != suite.sha256:
        raise ValueError("Suite definition differs from the published suite")
    if manifest.get("mode") not in {"realtime", "exhibition"}:
        raise ValueError("Invalid mode")
    if manifest.get("environment", {}).get("evaluator_version") != __version__:
        raise ValueError("Evaluator version differs; use the matching benchmark release")
    if replay and manifest["environment"]["evaluator_sha256"] != environment()["evaluator_sha256"]:
        raise ValueError("Evaluator source differs; use the original pinned image or checkout")
    expected = {f"{game}-{seed}": (game, seed) for game in suite.games for seed in suite.seeds}
    episode_root = root / "episodes"
    if episode_root.is_symlink() or not episode_root.is_dir():
        raise ValueError("Missing episode directory")
    if {path.name for path in episode_root.iterdir()} != set(expected):
        raise ValueError("Incomplete or unexpected episode set")
    agent = manifest.get("agent", {})
    if not isinstance(agent.get("name"), str) or not re.fullmatch(
        r"[A-Za-z0-9_-]{1,80}", agent["name"]
    ):
        raise ValueError("Invalid agent name")
    if (
        not isinstance(agent.get("revision"), str)
        or not 1 <= len(agent["revision"]) <= 300
        or not isinstance(manifest.get("hardware_description"), str)
        or not 1 <= len(manifest["hardware_description"]) <= 300
    ):
        raise ValueError("Missing agent revision or hardware description")
    rows, roots, allowed = [], {}, {"submission.json", "report.md"}
    for name, (game, seed) in expected.items():
        directory = episode_root / name
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("Invalid episode directory")
        files = _episode_files(directory)
        allowed.update(file.relative_to(root).as_posix() for file in files)
        ledger = read_ledger(directory / "events.jsonl")
        first, result = ledger[0], ledger[-1]
        if any(
            first.get(key) != value
            for key, value in {
                "agent": agent["name"],
                "game": game,
                "seed": seed,
                "max_steps": suite.max_steps,
                "mode": manifest["mode"],
                "version": __version__,
                "trust": "local-unattested",
            }.items()
        ):
            raise ValueError(f"Episode does not match the campaign: {name}")
        if _read_json(directory / "result.json") != result:
            raise ValueError("Result file differs from its evidence ledger")
        if len(files) != len(ledger) or {
            file.relative_to(directory).as_posix() for file in files
        } != {
            "events.jsonl",
            "result.json",
            *(f"frames/{i:04d}.png" for i in range(len(ledger) - 2)),
        }:
            raise ValueError("Missing or unexpected episode frames")
        verify_episode(directory, replay=replay)
        roots[name] = file_sha256(directory / "events.jsonl")
        rows.append(result)
    if manifest.get("episode_sha256") != roots:
        raise ValueError("Submission evidence roots do not match")
    ranking = summarize(rows, list(suite.games), list(suite.seeds))
    if manifest.get("ranking") != ranking:
        raise ValueError("Submitted ranking differs from verified episode results")
    for path in root.rglob("*"):
        if path.is_symlink() or (
            path.is_file() and path.relative_to(root).as_posix() not in allowed
        ):
            raise ValueError("Unexpected file in submission")
    return {
        "valid": True,
        "format": FORMAT,
        "suite": suite.id,
        "agent": agent["name"],
        "episodes": len(rows),
        "replayed": replay,
        "authentication": "local-unattested",
        "ranking": ranking,
    }


def verify_submission(path, replay=True):
    """Inspect an archive with strict paths, no links, size bounds and no agent execution."""
    path = Path(path)
    if path.is_dir():
        return _validate_directory(path, replay)
    if path.stat().st_size > MAX_TOTAL:
        raise ValueError("Submission archive exceeds 8 GiB")
    if not zipfile.is_zipfile(path):
        raise ValueError("Submission must be a ZIP archive")
    with (
        zipfile.ZipFile(path) as archive,
        tempfile.TemporaryDirectory(prefix="ggbench-review-") as tmp,
    ):
        members = archive.infolist()
        if len(members) > MAX_FILES or sum(m.file_size for m in members) > MAX_TOTAL:
            raise ValueError("Submission archive exceeds extraction limits")
        names = set()
        for member in members:
            name = member.filename
            parts = PurePosixPath(name).parts
            if (
                not name
                or "\\" in name
                or name.startswith("/")
                or ".." in parts
                or PurePosixPath(name).as_posix() != name
                or name in names
                or member.is_dir()
                or member.flag_bits & 1
                or stat.S_ISLNK(member.external_attr >> 16)
                or member.file_size > MAX_MEMBER
                or not (
                    name in {"submission.json", "report.md"}
                    or re.fullmatch(
                        r"episodes/[A-Za-z0-9_-]+/(?:events\.jsonl|result\.json|frames/[0-9]{4,}\.png)",
                        name,
                    )
                )
            ):
                raise ValueError("Unsafe or unexpected archive member")
            names.add(name)
            output = Path(tmp) / name
            output.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, output.open("xb") as target:
                written = 0
                while block := source.read(1024 * 1024):
                    written += len(block)
                    if written > member.file_size or written > MAX_MEMBER:
                        raise ValueError("Archive member exceeds its declared size")
                    target.write(block)
                if written != member.file_size:
                    raise ValueError("Truncated archive member")
        return _validate_directory(Path(tmp), replay)


def prepare_uploads(archive_path, directory):
    """Make browser-uploadable ZIP parts below GitHub's 25 MB attachment limit."""
    archive_path, directory = Path(archive_path), Path(directory)
    size, sha256 = archive_path.stat().st_size, file_sha256(archive_path)
    count = (size + UPLOAD_CHUNK - 1) // UPLOAD_CHUNK
    directory.mkdir(exist_ok=True)
    expected = {f"submission-part-{index + 1:03d}.zip" for index in range(count)}
    if any(path.is_symlink() or path.name not in expected for path in directory.iterdir()):
        raise ValueError("Unexpected file in upload directory")
    outputs = []
    with archive_path.open("rb") as source:
        for index in range(count):
            payload = source.read(UPLOAD_CHUNK)
            metadata = {
                "format": PART_FORMAT,
                "index": index,
                "count": count,
                "archive_bytes": size,
                "archive_sha256": sha256,
                "payload_sha256": digest(payload),
            }
            path = directory / f"submission-part-{index + 1:03d}.zip"
            if path.exists():
                with zipfile.ZipFile(path) as existing:
                    if (
                        sorted(existing.namelist()) != ["part.json", "payload.bin"]
                        or existing.getinfo("part.json").file_size > 4096
                        or existing.getinfo("payload.bin").file_size != len(payload)
                        or existing.read("part.json") != canonical(metadata)
                        or digest(existing.read("payload.bin")) != metadata["payload_sha256"]
                    ):
                        raise ValueError("Existing upload part differs from the original archive")
            else:
                with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_STORED) as output:
                    output.writestr("part.json", canonical(metadata))
                    output.writestr("payload.bin", payload)
            outputs.append(path)
    return outputs


def verify_uploads(paths, replay=True):
    paths = [Path(path) for path in paths]
    if len(paths) == 1 and paths[0].is_dir() and not (paths[0] / "submission.json").exists():
        paths = sorted(paths[0].glob("submission-part-*.zip"))
    if not paths:
        raise ValueError("No submission ZIPs found")
    if len(paths) == 1:
        if paths[0].is_dir():
            return verify_submission(paths[0], replay)
        with zipfile.ZipFile(paths[0]) as archive:
            if "part.json" not in archive.namelist():
                return verify_submission(paths[0], replay)
    if len(paths) > 512:
        raise ValueError("Too many upload parts")
    parts, identity = {}, None
    for path in paths:
        if path.stat().st_size > UPLOAD_CHUNK + 8192:
            raise ValueError("Upload part is too large")
        with zipfile.ZipFile(path) as archive:
            if sorted(archive.namelist()) != ["part.json", "payload.bin"]:
                raise ValueError("Invalid upload part contents")
            if (
                archive.getinfo("part.json").file_size > 4096
                or archive.getinfo("payload.bin").file_size > UPLOAD_CHUNK
            ):
                raise ValueError("Oversized upload part member")
            meta = json.loads(archive.read("part.json"))
        if (
            meta.get("format") != PART_FORMAT
            or any(type(meta.get(key)) is not int for key in ("index", "count", "archive_bytes"))
            or not 0 <= meta["index"] < meta["count"] <= 512
            or not 0 < meta["archive_bytes"] <= MAX_TOTAL
            or not re.fullmatch(r"[0-9a-f]{64}", str(meta.get("archive_sha256", "")))
            or not re.fullmatch(r"[0-9a-f]{64}", str(meta.get("payload_sha256", "")))
        ):
            raise ValueError("Invalid upload part metadata")
        current = (meta["count"], meta["archive_bytes"], meta["archive_sha256"])
        if identity is not None and identity != current:
            raise ValueError("Upload parts belong to different submissions")
        identity = current
        if meta["index"] in parts:
            raise ValueError("Duplicate upload part")
        parts[meta["index"]] = (path, meta)
    if len(parts) != identity[0]:
        raise ValueError(f"Missing upload parts: received {len(parts)} of {identity[0]}")
    with tempfile.TemporaryDirectory(prefix="ggbench-parts-") as tmp:
        joined = Path(tmp) / "submission.zip"
        size = 0
        with joined.open("xb") as output:
            for index in sorted(parts):
                path, meta = parts[index]
                with zipfile.ZipFile(path) as archive:
                    payload = archive.read("payload.bin")
                if digest(payload) != meta["payload_sha256"]:
                    raise ValueError("Upload part checksum mismatch")
                size += len(payload)
                if size > identity[1]:
                    raise ValueError("Upload exceeds declared archive size")
                output.write(payload)
        if size != identity[1] or file_sha256(joined) != identity[2]:
            raise ValueError("Reassembled archive checksum mismatch")
        return verify_submission(joined, replay)


def _report(manifest):
    rank = manifest["ranking"][0]
    return (
        f"# GeneralGameBench submission: {manifest['agent']['name']}\n\n"
        f"Suite: {manifest['suite']['id']} · mode: {manifest['mode']}\n\n"
        f"Score: {rank['score']}/100 across {rank['episodes']} episodes. "
        f"Maximum response: {rank['max_ms']:.3f} ms. "
        f"Sub-100 ms eligible: {rank['latency_eligible']}. "
        f"Aborted episodes: {rank['aborted_episodes']}.\n\n"
        "Every episode was replayed locally before packaging. Results remain local-unattested; "
        "successful replay does not authenticate hardware, timing or the operator. "
        "Compare only matching suites, versions, runtimes, hardware and modes.\n\n"
        "## Submit for community review\n\n"
        "Open https://github.com/DanielTea/generalgamebench/issues/new?template=submission.yml "
        "and attach every ZIP in the uploads folder (or link a public download of submission.zip). "
        "Describe the agent/model revision, hardware, training overlap and external services. "
        "This command has not uploaded anything or opened an issue. "
        "Maintainers review data; submitted agent code is never automatically executed.\n"
    )


def package_submission(root, destination):
    root, destination = Path(root), Path(destination)
    _validate_directory(root, replay=True)
    if destination.exists():
        raise FileExistsError("Submission archive already exists; preserve the original")
    files = [root / "submission.json", root / "report.md"]
    files += sorted(path for path in (root / "episodes").rglob("*") if path.is_file())
    if len(files) > MAX_FILES or sum(path.stat().st_size for path in files) > MAX_TOTAL:
        raise ValueError("Submission exceeds archive limits")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(
            destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6
        ) as archive:
            for path in files:
                archive.write(path, path.relative_to(root).as_posix())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return {
        "path": str(destination),
        "sha256": file_sha256(destination),
        "bytes": destination.stat().st_size,
    }


def _finish_bundle(output, manifest):
    path = output / "submission.zip"
    archive = {"path": str(path), "sha256": file_sha256(path), "bytes": path.stat().st_size}
    uploads = prepare_uploads(path, output / "uploads")
    (output / "SHA256SUMS").write_text(
        f"{archive['sha256']}  submission.zip\n"
        + "".join(f"{file_sha256(part)}  uploads/{part.name}\n" for part in uploads)
    )
    link = (
        ISSUE_URL
        + "?"
        + urlencode(
            {
                "template": "submission.yml",
                "title": f"[Agent] {manifest['agent']['name']} — {manifest['suite']['id']}",
            }
        )
    )
    (output / "SUBMIT.txt").write_text(
        f"Open this form and attach all {len(uploads)} ZIP files in the uploads folder:\n{link}\n\nNothing has been uploaded automatically.\n"
    )
    return {"archive": archive, "submission_url": link, "ranking": manifest["ranking"]}


def benchmark(
    suite_id,
    output,
    *,
    agent="react",
    agent_command=None,
    name=None,
    agent_revision=None,
    hardware=None,
    mode="exhibition",
    resume=False,
    progress=print,
):
    from .doctor import diagnose

    suite, output = SUITES[suite_id], Path(output)
    name = name or agent
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name):
        raise ValueError("Agent name must use 1–80 letters, digits, hyphens or underscores")
    if agent_command and (not agent_revision or not hardware):
        raise ValueError(
            "Custom agents require --agent-revision and --hardware for reproducibility"
        )
    for value in (agent_revision, hardware):
        if value and (len(value) > 300 or any(ord(char) < 32 for char in value)):
            raise ValueError("Revision and hardware labels must be short, single-line text")
    if mode not in {"realtime", "exhibition"}:
        raise ValueError("Unknown mode")
    command = (
        shlex.split(agent_command)
        if agent_command
        else [sys.executable, "-m", "generalgamebench.baselines", agent]
    )
    identity = {
        "name": name,
        "revision": agent_revision or file_sha256(Path(__file__).with_name("baselines.py")),
        "command_sha256": digest(canonical(command)),
        "kind": "custom" if agent_command else "bundled-baseline",
    }
    plan = {
        "format": FORMAT,
        "suite": suite.definition(),
        "suite_sha256": suite.sha256,
        "mode": mode,
        "agent": identity,
        "environment": environment(),
        "hardware_description": hardware or "Not specified; bundled baseline demonstration",
        "trust": "local-unattested",
    }
    if output.exists():
        if not resume or _read_json(output / "campaign.json") != plan:
            raise ValueError(
                "Output exists. Use --resume with the original configuration, or a new output directory"
            )
        if (output / "submission.zip").exists():
            verify_submission(output / "submission.zip")
            with zipfile.ZipFile(output / "submission.zip") as archive:
                manifest = json.loads(archive.read("submission.json"))
            if any(manifest.get(key) != value for key, value in plan.items()):
                raise ValueError("Existing archive differs from the original campaign")
            return _finish_bundle(output, manifest)
    else:
        checks = diagnose(suite_id)
        if not checks["ready"]:
            missing = "; ".join(item["detail"] for item in checks["checks"] if not item["ready"])
            raise ValueError(f"Suite is not installed: {missing}")
        output.mkdir(parents=True)
        _write_json(output / "campaign.json", plan)
    data = output / "submission"
    episodes = data / "episodes"
    episodes.mkdir(parents=True, exist_ok=True)
    expected = {f"{game}-{seed}" for game in suite.games for seed in suite.seeds}
    if any(path.name not in expected for path in episodes.iterdir()):
        raise ValueError("Unexpected episodes in campaign directory")
    results, roots = [], {}
    total, current = len(suite.games) * len(suite.seeds), 0
    for game in suite.games:
        for seed in suite.seeds:
            current += 1
            episode = episodes / f"{game}-{seed}"
            progress(f"[{current}/{total}] {game}, seed {seed}")
            if episode.exists():
                if not (episode / "result.json").is_file():
                    raise ValueError(
                        f"Interrupted episode retained at {episode}. Preserve this campaign and start a new output; partial attempts cannot be silently discarded"
                    )
                result = read_ledger(episode / "events.jsonl")[-1]
            else:
                participant = ProcessAgent(command)
                try:
                    result = run_episode(
                        participant, name, game, seed, episode, suite.max_steps, mode
                    )
                finally:
                    participant.close()
            results.append(result)
            roots[episode.name] = file_sha256(episode / "events.jsonl")
    manifest = {
        **plan,
        "episode_sha256": roots,
        "ranking": summarize(results, list(suite.games), list(suite.seeds)),
    }
    _write_json(data / "submission.json", manifest)
    (data / "report.md").write_text(_report(manifest))
    package_submission(data, output / "submission.zip")
    return _finish_bundle(output, manifest)
