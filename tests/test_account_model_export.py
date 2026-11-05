import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def exporter(monkeypatch):
    scripts = Path(__file__).parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location(
        "account_export", scripts / "export_account_models.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preserves_existing_report(exporter, tmp_path):
    (tmp_path / "previous-snapshot.json").write_text("original")
    with pytest.raises(FileExistsError):
        exporter.export(tmp_path)
    assert (tmp_path / "previous-snapshot.json").read_text() == "original"


def test_rejects_silent_model_substitution_and_tool_use(exporter, tmp_path):
    from generalgamebench.model_prompt import PROMPT_VERSION
    from generalgamebench.runner import run_episode

    class Agent:
        model = "claude-haiku-5-5"
        metadata = {
            "requested_model": model,
            "resolved_models": [model],
            "prompt_version": PROMPT_VERSION,
            "transport": "authenticated-cli-per-frame",
            "observation": "png-only",
            "reasoning_effort": "low",
            "tool_events": 0,
        }

        def act(self, obs, timeout):
            return {"nonce": obs["nonce"], "action": 0}

    entry = {"provider": "claude", "model": Agent.model}
    row = run_episode(
        Agent(),
        exporter.model_id(entry),
        "coin-run",
        3000,
        tmp_path / "episode",
        2,
        "exhibition",
        120,
    )
    campaign = {
        "mode": "exhibition",
        "version": row["version"],
        "max_steps": 2,
        "timeout_s": 120,
        "prompt_version": PROMPT_VERSION,
    }
    exporter.check_result(row, entry, campaign, "coin-run", 3000)
    row["provider_metadata"]["resolved_models"] = ["claude-haiku-4-5-20251001"]
    with pytest.raises(ValueError, match="different model"):
        exporter.check_result(row, entry, campaign, "coin-run", 3000)
    row["provider_metadata"]["resolved_models"] = [Agent.model]
    row["provider_metadata"]["tool_events"] = 1
    with pytest.raises(ValueError, match="run setting"):
        exporter.check_result(row, entry, campaign, "coin-run", 3000)
