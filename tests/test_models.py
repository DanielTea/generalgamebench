import pytest

from generalgamebench.models import parse_action


@pytest.mark.parametrize("value", ["[]", '{"action":true}', '{"action":1,"reward":99}', "hello"])
def test_model_invalid_output(value):
    with pytest.raises(ValueError):
        parse_action(value)


def test_model_json_and_fence():
    assert parse_action('{"action":2}') == 2
    assert parse_action('```json\n{"action":0}\n```') == 0


@pytest.mark.parametrize(
    "model,effort", [("claude-haiku-5-5", "low"), ("claude-haiku-4-5-20251001", "default")]
)
def test_haiku_effort_matches_model_support(monkeypatch, model, effort):
    import json
    from types import SimpleNamespace

    from generalgamebench.models import CLIModelAgent

    def call(command, **kwargs):
        assert ("--effort" in command) == (effort == "low")
        if effort == "low":
            assert command[command.index("--effort") + 1] == "low"
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"type": "result", "result": '{"action":0}'}),
        )

    monkeypatch.setattr("generalgamebench.models.subprocess.run", call)
    agent = CLIModelAgent("claude", model)
    try:
        assert agent.metadata["reasoning_effort"] == effort
        assert agent.act(
            {"nonce": "test", "image_png": "", "actions": ["wait"], "instructions": "Wait."},
            120,
        ) == {"nonce": "test", "action": 0}
    finally:
        agent.close()
