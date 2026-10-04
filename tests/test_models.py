import pytest

from screenquest_arena.models import parse_action


@pytest.mark.parametrize("value", ["[]", '{"action":true}', '{"action":1,"reward":99}', "hello"])
def test_model_invalid_output(value):
    with pytest.raises(ValueError):
        parse_action(value)


def test_model_json_and_fence():
    assert parse_action('{"action":2}') == 2
    assert parse_action('```json\n{"action":0}\n```') == 0
