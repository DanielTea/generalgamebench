import copy
import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def exporter(monkeypatch):
    scripts = Path(__file__).parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("jev_export", scripts / "export_jev.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_container_id_change_requires_exact_trace_proof_and_preserves_metadata(exporter):
    original = {"task": {"container_image": "sha256:old", "engine_revision": "pinned"}}
    current = {"task": {"container_image": "sha256:new", "engine_revision": "pinned"}}
    preserved = copy.deepcopy((original, current))
    with pytest.raises(ValueError, match="rebuild replay audit"):
        exporter.compare_tasks(original, current, {})
    proof = {
        "task": {
            "original_metadata": original["task"],
            "rebuilt_metadata": current["task"],
            "exact_frames": 8,
            "exact_native_score": True,
        }
    }
    exporter.compare_tasks(original, current, proof)
    assert (original, current) == preserved
    current["task"]["engine_revision"] = "different-source"
    with pytest.raises(ValueError, match="rebuild replay audit"):
        exporter.compare_tasks(original, current, proof)


def test_jev_export_refuses_to_replace_existing_snapshot(exporter, tmp_path):
    (tmp_path / "previous-snapshot.json").write_text("original")
    with pytest.raises(FileExistsError):
        exporter.export(tmp_path)
    assert (tmp_path / "previous-snapshot.json").read_text() == "original"
