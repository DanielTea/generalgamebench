"""Native TypeSafe image decisions. Provider credentials never enter evidence."""

import base64
import http.client
import json
import os
import secrets
import time

from .model_prompt import PROMPT_VERSION, format_prompt
from .models import ProviderUnavailable
from .protocol import ProtocolError

TRANSPORT = "persistent-typesafe-https-multipart"
ACTION_SCHEMA = "native-choice/1"
MAX_RESPONSE = 1024 * 1024


class JevAgent:
    """One native Choice call per PNG, with no retries or fallback actions."""

    def __init__(self, model, api_key=None):
        self.model = model
        self._key = api_key or os.environ.get("TYPESAFE_API_KEY")
        if not self._key:
            raise ValueError("Configure TYPESAFE_API_KEY before calling Jev")
        self._connection = None
        self.metadata = {
            "transport": TRANSPORT,
            "requested_model": model,
            "prompt_version": PROMPT_VERSION,
            "action_schema": ACTION_SCHEMA,
            "observation": "png-only",
            "images_header": True,
            "retries": 0,
            "tool_events": 0,
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
        }

    def _request(self, method, path, body, content_type, timeout):
        if timeout <= 0:
            raise TimeoutError("Jev response deadline exceeded")
        if self._connection is None:
            self._connection = http.client.HTTPSConnection("api.typesafe.ai", timeout=timeout)
        connection = self._connection
        connection.timeout = timeout
        if connection.sock is not None:
            connection.sock.settimeout(timeout)
        try:
            connection.request(
                method,
                path,
                body=body,
                headers={
                    "Authorization": "Bearer " + self._key,
                    "Content-Type": content_type,
                    "TypeSafe-Danger-Zone-Images": "true",
                },
            )
            response = connection.getresponse()
            payload = response.read(MAX_RESPONSE + 1)
            if response.status != 200:
                # Provider bodies can contain account details. Never persist them.
                raise ProviderUnavailable(f"TypeSafe HTTP {response.status}")
            if len(payload) > MAX_RESPONSE:
                raise ProtocolError("Oversized TypeSafe response")
            value = json.loads(payload)
            if not isinstance(value, dict):
                raise ProtocolError("Invalid TypeSafe response")
            return value
        except (OSError, http.client.HTTPException) as exc:
            self.close()
            if isinstance(exc, TimeoutError):
                raise TimeoutError("Jev response deadline exceeded") from None
            raise ProviderUnavailable("TypeSafe transport failed") from None
        except (ValueError, ProviderUnavailable):
            self.close()
            raise

    def list_models(self, timeout=30):
        return self._request("GET", "/v1/models", None, "application/json", timeout)

    def act(self, obs, timeout):
        started = time.perf_counter()
        reference = secrets.token_hex(16)
        request = {
            "model": self.metadata["requested_model"],
            "state": {"screenshot": reference},
            "assets": {reference: {"type": "image", "part": "screenshot"}},
            "questions": {
                "action": {
                    "type": "choice",
                    "instructions": format_prompt(obs),
                    "criteria": {str(i): action for i, action in enumerate(obs["actions"])},
                }
            },
        }
        boundary = "ggbench-" + secrets.token_hex(16)
        body = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="request"\r\n'
            "Content-Type: application/json\r\n\r\n"
        ).encode()
        body += json.dumps(request, separators=(",", ":")).encode()
        body += (
            f"\r\n--{boundary}\r\nContent-Disposition: form-data; "
            'name="screenshot"; filename="frame.png"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode()
        body += base64.b64decode(obs["image_png"], validate=True)
        body += f"\r\n--{boundary}--\r\n".encode()
        self.metadata["calls"] += 1
        value = self._request(
            "POST",
            "/v1/systemone",
            body,
            "multipart/form-data; boundary=" + boundary,
            timeout - (time.perf_counter() - started),
        )
        resolved = value.get("model")
        if not isinstance(resolved, str) or not resolved.startswith("jev-"):
            raise ProtocolError("TypeSafe did not identify its model")
        requested = self.metadata["requested_model"]
        if requested not in {"jev-latest", "jev-preview"} and resolved != requested:
            raise ProtocolError("TypeSafe returned a different model")
        self.model = resolved
        self.metadata["resolved_models"] = [resolved]
        try:
            answer = value["answers"]["action"]
            choice = answer["choice"]
            if (
                answer["type"] != "choice"
                or choice not in request["questions"]["action"]["criteria"]
            ):
                raise ProtocolError("TypeSafe returned an invalid action")
            for field in ("input_tokens", "output_tokens"):
                tokens = value["usage"][field]
                if type(tokens) is not int or tokens < 0:
                    raise ProtocolError("TypeSafe returned invalid token usage")
                self.metadata[field] += tokens
        except (KeyError, TypeError):
            raise ProtocolError("TypeSafe returned an invalid decision") from None
        return {"nonce": obs["nonce"], "action": int(choice)}

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None
