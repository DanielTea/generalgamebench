"""Opt-in authenticated CLI exhibition adapters. Credentials never enter evidence."""

import base64
import json
import os
import subprocess
import tempfile
from pathlib import Path

from .model_prompt import PROMPT_VERSION, format_prompt
from .protocol import ProtocolError

SCHEMA = {
    "type": "object",
    "properties": {"action": {"type": "integer"}},
    "required": ["action"],
    "additionalProperties": False,
}


class ProviderUnavailable(ProtocolError):
    """The transport failed without a usable model response."""


def parse_action(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    value = json.loads(cleaned)
    if not isinstance(value, dict) or set(value) != {"action"} or type(value["action"]) is not int:
        raise ProtocolError("Model must return a single integer action")
    return value["action"]


class CLIModelAgent:
    """Slow fresh CLI call per frame, with startup inside the measured latency.

    This is an exhibition integration, not a low-latency provider benchmark.
    """

    def __init__(self, provider: str, model: str):
        if provider not in {"astra", "openai", "claude"}:
            raise ValueError("Unknown provider")
        self.provider, self.model = provider, model
        self.metadata = {
            "transport": "authenticated-cli-per-frame",
            "requested_model": model,
            "tool_events": 0,
            "observation": "png-only",
            "calls": 0,
            "prompt_version": PROMPT_VERSION,
        }
        self.temp = tempfile.TemporaryDirectory(prefix="arena-model-")
        self.cwd = Path(self.temp.name)
        (self.cwd / "schema.json").write_text(json.dumps(SCHEMA))

    def act(self, obs, timeout):
        prompt = format_prompt(obs)
        if self.provider == "claude":
            cmd = [
                "claude",
                "-p",
                "--model",
                self.model,
                "--tools",
                "",
                "--strict-mcp-config",
                "--mcp-config",
                '{"mcpServers":{}}',
                "--no-session-persistence",
                "--disable-slash-commands",
                "--restricted",
                "--effort",
                "low",
                "--input-format",
                "stream-json",
                "--output-format",
                "stream-json",
                "--verbose",
            ]
            if "haiku" in self.model:
                index = cmd.index("--effort")
                del cmd[index : index + 2]
            payload = {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": obs["image_png"],
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                },
            }
            data = json.dumps(payload) + "\n"
        else:
            frame = self.cwd / "frame.png"
            frame.write_bytes(base64.b64decode(obs["image_png"]))
            cmd = [
                "codex",
                "exec",
                "--ignore-user-config",
                "--ephemeral",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--model",
                self.model,
                "-c",
                'model_reasoning_effort="low"',
                "-c",
                "features.shell_tool=false",
                "--image",
                str(frame),
                "--output-schema",
                str(self.cwd / "schema.json"),
                "--json",
                "-",
            ]
            data = prompt
        env = os.environ.copy()
        # Do not nest Claude/Codex session identities inside an exhibition process.
        env.pop("CLAUDECODE", None)
        try:
            response = subprocess.run(
                cmd,
                input=data,
                text=True,
                capture_output=True,
                cwd=self.cwd,
                env=env,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("Model CLI exceeded exhibition deadline") from exc
        if response.returncode:
            # Do not leak provider errors, local paths, account info or credentials into evidence.
            raise ProviderUnavailable(f"{self.provider} CLI exited {response.returncode}")
        self.metadata["calls"] += 1
        if self.provider == "claude":
            claude_events = [
                json.loads(line) for line in response.stdout.splitlines() if line.strip()
            ]
            tool_events = [
                block
                for event in claude_events
                for block in event.get("message", {}).get("content", [])
                if isinstance(block, dict) and block.get("type") == "tool_use"
            ]
            if tool_events:
                self.metadata["tool_events"] += len(tool_events)
                raise ProtocolError("Tool use invalidates pixels-only exhibition")
            value = next((e for e in reversed(claude_events) if e.get("type") == "result"), {})
            if not value:
                raise ProtocolError("Claude produced no result")
            if value.get("is_error"):
                raise ProviderUnavailable("Claude returned a provider error")
            models = list(value.get("modelUsage", {}))
            self.metadata["resolved_models"] = models
            if models:
                self.model = models[0]
            text = value.get("result", "")
        else:
            events = [json.loads(line) for line in response.stdout.splitlines() if line.strip()]
            items = [e["item"] for e in events if e.get("type") == "item.completed"]
            forbidden = [
                i
                for i in items
                if i.get("type")
                in {"command_execution", "mcp_tool_call", "web_search", "file_change"}
            ]
            if forbidden:
                self.metadata["tool_events"] += len(forbidden)
                raise ProtocolError("Tool use invalidates pixels-only exhibition")
            messages = [i["text"] for i in items if i.get("type") == "agent_message"]
            if not messages:
                raise ProtocolError("Astra produced no final action")
            text = messages[-1]
        action = parse_action(text)
        return {"nonce": obs["nonce"], "action": action}

    def close(self):
        self.temp.cleanup()
