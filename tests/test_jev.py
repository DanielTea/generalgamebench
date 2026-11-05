import base64
import io
import json
from email.parser import BytesParser
from email.policy import default

import pytest

from generalgamebench.jev import JevAgent, prepare_image
from generalgamebench.models import ProviderUnavailable
from generalgamebench.protocol import ProtocolError


def observation():
    from PIL import Image

    png = io.BytesIO()
    Image.new("RGB", (280, 280), "gray").save(png, format="PNG")
    return {
        "image_png": base64.b64encode(png.getvalue()).decode(),
        "nonce": "fresh-nonce",
        "instructions": "Collect the coin.",
        "actions": ["wait", "left", "right"],
    }


def response(**changes):
    return {
        "model": "jev-1.14.0",
        "answers": {"action": {"type": "choice", "choice": "2"}},
        "usage": {"input_tokens": 100, "output_tokens": 3},
        **changes,
    }


def test_native_image_and_actions_are_sent_without_private_state(monkeypatch):
    agent = JevAgent("jev-1.14.0", api_key="private-test-key")
    sent = []

    def request(method, path, body, content_type, timeout):
        sent.append((body, content_type))
        assert method == "POST" and path == "/v1/systemone" and timeout > 0
        return response()

    monkeypatch.setattr(agent, "_request", request)
    obs = {**observation(), "seed": 999, "reward": 42, "coordinates": [10, 20]}
    assert agent.act(obs, 10) == {"nonce": "fresh-nonce", "action": 2}
    body, content_type = sent[0]
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + body
    )
    parts = list(message.iter_parts())
    request_json = json.loads(parts[0].get_payload(decode=True))
    assert parts[1].get_payload(decode=True) == base64.b64decode(obs["image_png"])
    assert request_json["questions"]["action"]["criteria"] == {
        "0": "wait",
        "1": "left",
        "2": "right",
    }
    assert list(request_json["assets"]) == [request_json["state"]["screenshot"]]
    assert b"fresh-nonce" not in body and b"coordinates" not in body
    assert b"private-test-key" not in body
    assert "private-test-key" not in json.dumps(agent.metadata)


@pytest.mark.parametrize(
    "value",
    [
        response(model="jev-1.13.0"),
        response(answers={"action": {"type": "choice", "choice": "99"}}),
        response(answers={"action": {"type": "choice", "choice": True}}),
        response(answers={}),
    ],
)
def test_wrong_model_and_invalid_actions_fail_without_substitution(monkeypatch, value):
    agent = JevAgent("jev-1.14.0", api_key="private-test-key")
    monkeypatch.setattr(agent, "_request", lambda *args: value)
    with pytest.raises(ProtocolError):
        agent.act(observation(), 10)


def test_http_failure_is_not_retried_or_written_to_metadata():
    class Response:
        status = 429

        def read(self, limit):
            return b"private account details"

    class Connection:
        sock = None
        requests = 0
        closed = False

        def request(self, method, path, body, headers):
            self.requests += 1
            assert headers["TypeSafe-Danger-Zone-Images"] == "true"
            assert headers["Authorization"] == "Bearer private-test-key"

        def getresponse(self):
            return Response()

        def close(self):
            self.closed = True

    agent = JevAgent("jev-1.14.0", api_key="private-test-key")
    connection = Connection()
    agent._connection = connection
    with pytest.raises(ProviderUnavailable, match="TypeSafe HTTP 429") as error:
        agent.act(observation(), 10)
    assert connection.requests == 1 and connection.closed
    assert "private" not in str(error.value)
    assert "private" not in json.dumps(agent.metadata)


def test_small_frames_repeat_original_pixels_without_cropping():
    from PIL import Image

    original = Image.new("RGB", (64, 64), "blue")
    original.putpixel((10, 20), (255, 0, 0))
    png = io.BytesIO()
    original.save(png, format="PNG")
    enlarged = Image.open(io.BytesIO(prepare_image(png.getvalue())))
    assert enlarged.size == (320, 320)
    for y in range(64):
        for x in range(64):
            block = enlarged.crop((x * 5, y * 5, (x + 1) * 5, (y + 1) * 5))
            assert block.tobytes() == bytes(original.getpixel((x, y))) * 25
