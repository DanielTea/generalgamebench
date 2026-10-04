import json

from generalgamebench.model_inventory import codex_models, local_models
from generalgamebench.registry import PROCGEN_RANGES, TASKS


def test_task_ids_and_scores_are_unambiguous():
    assert len(PROCGEN_RANGES) == 16
    for key, task in TASKS.items():
        assert key == task.id
        assert task.score_range[1] > task.score_range[0]
        assert task.task_version


def test_discovery_excludes_hidden_and_text_only_models(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    (tmp_path / "models_cache.json").write_text(
        json.dumps(
            {
                "models": [
                    {"slug": "visible-vision", "visibility": "list", "input_modalities": ["image"]},
                    {"slug": "hidden-vision", "visibility": "hide", "input_modalities": ["image"]},
                    {"slug": "visible-text", "visibility": "list", "input_modalities": ["text"]},
                ]
            }
        )
    )
    assert [m["model"] for m in codex_models()] == ["visible-vision"]


def test_local_discovery_rejects_incomplete_weight_shards(tmp_path, monkeypatch):
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path))
    snapshot = tmp_path / "models--mlx-community--example" / "snapshots" / "revision"
    snapshot.mkdir(parents=True)
    (snapshot / "config.json").write_text('{"vision_config":{"size":1},"model_type":"qwen3_5"}')
    (snapshot / "first.safetensors").write_bytes(b"first")
    (snapshot / "model.safetensors.index.json").write_text(
        json.dumps({"weight_map": {"a": "first.safetensors", "b": "missing.safetensors"}})
    )
    assert local_models() == []
    (snapshot / "missing.safetensors").write_bytes(b"second")
    assert local_models()[0]["revision"] == "revision"
