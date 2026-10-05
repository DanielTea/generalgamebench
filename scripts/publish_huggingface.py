"""Publish a verified export: Dataset first, then a Space pinned to that commit.

Run only for an explicitly authorized publication. Authentication is read by
huggingface_hub from HF_TOKEN or its normal local token store, never CLI arguments.
"""

import argparse
import hashlib
import html
import json
import re
import tempfile
from pathlib import Path


def verify_export(directory):
    directory = directory.resolve()
    manifest = json.loads((directory / "manifest.json").read_text())
    actual = {
        str(path.relative_to(directory))
        for path in directory.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if actual != set(manifest):
        raise ValueError("Export file inventory differs from manifest; export again")
    for name, digest in manifest.items():
        path = directory / name
        if path.is_symlink() or not path.resolve().is_relative_to(directory):
            raise ValueError("Export must contain only regular files within its directory")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Export checksum differs: {name}")
    publication = json.loads((directory / "publication.json").read_text())
    for relative in ("space/data.json", "dataset/snapshot.json"):
        if manifest[relative] != publication["snapshot_sha256"]:
            raise ValueError("Space and Dataset snapshots must match")
    return publication


def bind_space(directory, publication):
    """Create commit-bound files outside the immutable export directory."""
    revision = publication["dataset_revision"]
    dataset_url = "https://huggingface.co/datasets/" + publication["dataset_id"]
    snapshot_url = f"{dataset_url}/resolve/{revision}/snapshot.json"
    readme = (directory / "space/README.md").read_text()
    readme += (
        f"\n## Published snapshot\n\n"
        f"[Exact Dataset revision]({dataset_url}/tree/{revision}) · "
        f"[Matching source snapshot]({snapshot_url})\n\n"
        f"Source commit: `{publication['source_commit']}`. "
        f"Snapshot SHA-256: `{publication['snapshot_sha256']}`.\n"
    )
    index = (directory / "space/index.html").read_text()
    notice = (
        '<p class="footnote" id="hub-publication">'
        f'<a href="{html.escape(dataset_url)}/tree/{revision}" target="_blank" '
        'rel="noopener">Explore this results Dataset</a> · '
        f'<a href="{html.escape(snapshot_url)}" target="_blank" rel="noopener">'
        f"Pinned snapshot {revision[:7]}</a>. "
        "Gaming leaderboard · community submissions reviewed by maintainers.</p>"
    )
    if "<!-- HUB_PUBLICATION -->" not in index:
        raise ValueError("Space HTML is missing its Dataset publication marker")
    index = index.replace("<!-- HUB_PUBLICATION -->", notice)
    return {
        "README.md": readme.encode(),
        "index.html": index.encode(),
        "publication.json": (json.dumps(publication, indent=2) + "\n").encode(),
    }


def publish(directory, source_commit, api):
    from huggingface_hub import CommitOperationAdd

    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("A full Git source commit is required")
    publication = verify_export(directory)
    publication["source_commit"] = source_commit
    # Validate all binding prerequisites before creating or changing remote repos.
    bind_space(directory, {**publication, "dataset_revision": "0" * 40})
    for kind, key in (("dataset", "dataset_id"), ("space", "space_id")):
        options = {"space_sdk": "static"} if kind == "space" else {}
        api.create_repo(publication[key], repo_type=kind, private=False, exist_ok=True, **options)
        info = api.repo_info(publication[key], repo_type=kind)
        if info.private:
            raise ValueError(f"Existing {kind} is private; select the intended public repository")
    dataset_commit = api.upload_folder(
        repo_id=publication["dataset_id"],
        repo_type="dataset",
        folder_path=directory / "dataset",
        commit_message=f"Publish measured results from {source_commit[:12]}",
    )
    publication["dataset_revision"] = dataset_commit.oid
    bound = bind_space(directory, publication)
    operations = [
        CommitOperationAdd(
            path_in_repo=str(path.relative_to(directory / "space")), path_or_fileobj=path
        )
        for path in sorted((directory / "space").rglob("*"))
        if path.is_file() and str(path.relative_to(directory / "space")) not in bound
    ]
    operations.extend(
        CommitOperationAdd(path_in_repo=name, path_or_fileobj=content)
        for name, content in bound.items()
    )
    space_commit = api.create_commit(
        repo_id=publication["space_id"],
        repo_type="space",
        operations=operations,
        commit_message=f"Publish leaderboard for Dataset {dataset_commit.oid[:12]}",
    )
    publication["space_revision"] = space_commit.oid
    return publication


if __name__ == "__main__":
    from huggingface_hub import HfApi

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", dest="directory", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.receipt.resolve().is_relative_to(args.directory.resolve()):
        parser.error("Save the publication receipt outside the immutable export")
    result = publish(args.directory, args.source_commit, HfApi())
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    # Replace the local receipt only once the complete publication succeeded.
    with tempfile.NamedTemporaryFile(mode="w", dir=args.receipt.parent, delete=False) as file:
        json.dump(result, file, indent=2)
        file.write("\n")
        temporary = Path(file.name)
    temporary.replace(args.receipt)
    print(json.dumps(result, indent=2))
