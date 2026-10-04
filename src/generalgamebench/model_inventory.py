"""Discover configured models, without reading or exporting secret values."""

import json
import os
import selectors
import subprocess
import tempfile
from pathlib import Path


def codex_models():
    path = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "models_cache.json"
    if not path.exists():
        return []
    return [
        {"provider": "openai", "model": m["slug"], "source": "configured-codex-model-list"}
        for m in json.loads(path.read_text()).get("models", [])
        if m.get("visibility") == "list" and "image" in m.get("input_modalities", [])
    ]


def claude_models():
    """Use the CLI's SDK initialization response, never account/credential fields."""
    with tempfile.TemporaryDirectory(prefix="ggbench-discovery-") as cwd:
        process = subprocess.Popen(
            [
                "claude",
                "-p",
                "--input-format",
                "stream-json",
                "--output-format",
                "stream-json",
                "--verbose",
                "--tools",
                "",
                "--strict-mcp-config",
                "--mcp-config",
                '{"mcpServers":{}}',
                "--no-session-persistence",
                "--restricted",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=cwd,
            env={k: v for k, v in os.environ.items() if k != "CLAUDECODE"},
            text=True,
        )
        try:
            process.stdin.write(
                json.dumps(
                    {
                        "type": "control_request",
                        "request_id": "model-list",
                        "request": {"subtype": "initialize"},
                    }
                )
                + "\n"
            )
            process.stdin.flush()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                if not selector.select(30):
                    raise TimeoutError("Claude model discovery timed out")
                data = json.loads(process.stdout.readline())
            models = data.get("response", {}).get("response", {}).get("models", [])
            unique = {}
            for m in models:
                model = m.get("resolvedModel")
                if model:
                    unique[model] = {
                        "provider": "claude",
                        "model": model,
                        "source": "configured-claude-model-list",
                    }
            return list(unique.values())
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            process.stdin.close()
            process.stdout.close()


def local_models():
    root = Path(os.environ.get("HF_HUB_CACHE", Path.home() / ".cache/huggingface/hub"))
    found = []
    for directory in sorted(root.glob("models--*")):
        refs = directory / "refs/main"
        revisions = (
            [refs.read_text().strip()]
            if refs.exists()
            else [p.name for p in sorted((directory / "snapshots").glob("*"))]
        )
        # A fully cached snapshot is required; never download weights implicitly.
        for revision in revisions:
            snapshot = directory / "snapshots" / revision
            config = snapshot / "config.json"
            if not config.exists() or not list(snapshot.glob("*.safetensors")):
                continue
            index = snapshot / "model.safetensors.index.json"
            if index.exists():
                shards = set(json.loads(index.read_text()).get("weight_map", {}).values())
                if any(not (snapshot / shard).is_file() for shard in shards):
                    continue
            data = json.loads(config.read_text())
            if not data.get("vision_config") or data.get("model_type") in {
                "clip",
                "siglip",
                "siglip2",
            }:
                continue
            if "mlx-community" not in directory.name:
                continue
            model = directory.name[len("models--") :].replace("--", "/")
            found.append(
                {
                    "provider": "mlx",
                    "model": model,
                    "revision": revision,
                    "source": "installed-huggingface-cache",
                    "local_path": str(snapshot),
                }
            )
    return found


def discover():
    errors, models = [], []
    for name, function in [
        ("openai", codex_models),
        ("claude", claude_models),
        ("mlx", local_models),
    ]:
        try:
            models.extend(function())
        except (OSError, ValueError, TimeoutError) as exc:
            errors.append({"provider": name, "error": type(exc).__name__})
    return {
        "models": models,
        "errors": errors,
        "scope": "configured vision models; availability requires a successful call",
    }
