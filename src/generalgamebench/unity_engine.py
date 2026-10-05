"""Pixels-only facade over a pinned Unity VisualFoodCollector executable.

Private vectors, agent IDs, action masks and rewards never become observations.
The executable is installed separately; no Unity editor is required.
"""

import hashlib
import json
import os
import platform
import socket
import tempfile
from pathlib import Path

import numpy as np


def unity_manifest(system=None, machine=None):
    system, machine = system or platform.system(), machine or platform.machine()
    if system == "Darwin":
        name = "assets.json"
    elif system == "Linux" and machine in {"x86_64", "AMD64"}:
        name = "assets-linux.json"
    else:
        raise RuntimeError("The Unity task requires macOS or Linux x86_64.")
    root = Path(__file__).resolve().parents[2]
    return json.loads((root / "environments/unity" / name).read_text())


def asset_digest(app):
    digest = hashlib.sha256()
    for path in sorted(app.rglob("*")):
        # The official executable writes profiler timings inside its app bundle.
        # These generated logs are not input assets and differ on every run.
        if (
            path.relative_to(app)
            .as_posix()
            .startswith(("Contents/ML-Agents/Timers/", "Startup_Data/ML-Agents/Timers/"))
        ):
            continue
        if path.is_file():
            digest.update(path.relative_to(app).as_posix().encode() + b"\0")
            file_digest = hashlib.sha256()
            with path.open("rb") as file:
                for chunk in iter(lambda: file.read(1024 * 1024), b""):
                    file_digest.update(chunk)
            digest.update(file_digest.digest())
    return digest.hexdigest()


class UnityPixelsEnv:
    actions = [
        "wait",
        "forward",
        "backward",
        "strafe_left",
        "strafe_right",
        "turn_left",
        "turn_right",
        "fire",
    ]

    def __init__(self, seed):
        from mlagents_envs.environment import UnityEnvironment
        from mlagents_envs.exception import UnityWorkerInUseException
        from mlagents_envs.side_channel.engine_configuration_channel import (
            EngineConfigurationChannel,
        )

        root = Path(__file__).resolve().parents[2]
        manifest = unity_manifest()
        app = Path(
            os.environ.get(
                "GGBENCH_UNITY_APP",
                root
                / manifest.get("install_directory", ".game-assets/unity")
                / manifest["application"],
            )
        )
        if not app.is_dir():
            raise RuntimeError("Install the pinned Unity example; see environments/unity")
        self.assets_sha256 = asset_digest(app)
        if self.assets_sha256 != manifest["app_tree_sha256"]:
            raise ValueError("Unity executable/assets differ from the pinned task")
        self.logs = tempfile.TemporaryDirectory(prefix="ggbench-unity-")
        self.env = None
        try:
            for attempt in range(3):
                with socket.socket() as sock:
                    sock.bind(("127.0.0.1", 0))
                    port = sock.getsockname()[1]
                channel = EngineConfigurationChannel()
                channel.set_configuration_parameters(
                    width=320, height=240, time_scale=1, capture_frame_rate=30
                )
                try:
                    self.env = UnityEnvironment(
                        file_name=str(app / manifest["executable"])
                        if "executable" in manifest
                        else str(app),
                        seed=seed,
                        base_port=port,
                        worker_id=0,
                        side_channels=[channel],
                        timeout_wait=60,
                        log_folder=self.logs.name,
                        additional_args=[
                            "--mlagents-scene-name",
                            "Assets/ML-Agents/Examples/FoodCollector/Scenes/VisualFoodCollector.unity",
                            "-batchmode",
                            *(["-force-glcore"] if platform.system() == "Linux" else []),
                        ],
                    )
                    break
                except UnityWorkerInUseException:
                    if attempt == 2:
                        raise
            self.env.reset()
            if len(self.env.behavior_specs) != 1:
                raise ValueError("Unexpected Unity behavior set")
            self.name = next(iter(self.env.behavior_specs))
            self.spec = self.env.behavior_specs[self.name]
            if self.spec.action_spec.continuous_size != 3 or tuple(
                self.spec.action_spec.discrete_branches
            ) != (2,):
                raise ValueError("Unexpected Unity controls")
            visuals = [
                i for i, spec in enumerate(self.spec.observation_specs) if spec.shape == (3, 84, 84)
            ]
            if len(visuals) != 1:
                raise ValueError("Expected one native RGB camera")
            self.visual = visuals[0]
            decisions, _ = self.env.get_steps(self.name)
            if not len(decisions):
                raise ValueError("Unity did not produce an initial observation")
            self.player = int(min(decisions.agent_id))
            self.initial = self._pixels(decisions[self.player])
            self.done = False
        except BaseException:
            self.close()
            raise

    def _pixels(self, record):
        pixels = record.obs[self.visual]
        if pixels.shape != (3, 84, 84) or not np.isfinite(pixels).all():
            raise ValueError("Invalid Unity camera output")
        return (np.clip(pixels.transpose(1, 2, 0), 0, 1) * 255).astype(np.uint8)

    def reset(self):
        return self.initial.copy()

    def step(self, action):
        if self.done or type(action) is not int or not 0 <= action < len(self.actions):
            raise ValueError("Illegal Unity action or finished episode")
        decisions, _ = self.env.get_steps(self.name)
        controls = self.spec.action_spec.empty_action(len(decisions))
        index = list(decisions.agent_id).index(self.player)
        if action in (1, 2):
            controls.continuous[index, 0] = 1 if action == 1 else -1
        elif action in (3, 4):
            controls.continuous[index, 1] = -1 if action == 3 else 1
        elif action in (5, 6):
            controls.continuous[index, 2] = 0.25 if action == 5 else -0.25
        elif action == 7:
            controls.discrete[index, 0] = 1
        self.env.set_actions(self.name, controls)
        for _ in range(100):
            self.env.step()
            decisions, terminals = self.env.get_steps(self.name)
            if self.player in terminals:
                self.done = True
                record = terminals[self.player]
                break
            if self.player in decisions:
                record = decisions[self.player]
                break
            # Other agents continue with no-op while awaiting this player's decision.
            self.env.set_actions(self.name, self.spec.action_spec.empty_action(len(decisions)))
        else:
            raise TimeoutError("Unity did not return the controlled player's decision")
        return self._pixels(record), float(record.reward), self.done, False, {}

    def close(self):
        if self.env is not None:
            self.env.close()
            self.env = None
        self.logs.cleanup()
