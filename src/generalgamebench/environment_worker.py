"""Trusted engine worker. Standalone so legacy engines can use Python 3.10.

JSON stdout is reserved for the referee; upstream diagnostics go to stderr.
Never send structured game observations, rewards or seeds to the model.
"""

import base64
import contextlib
import importlib.metadata
import io
import json
import os
import sys
import tempfile
import traceback

import numpy as np
from PIL import Image


class Environment:
    def __init__(self, task, seed, max_steps):
        self.task, self.seed, self.max_steps = task, seed, max_steps
        self.t, self.raw, self.done = 0, 0.0, False
        self.metrics = {}
        self.kind = task["id"]
        self.instructions = task["objective"]
        self.engine = None
        if self.kind.startswith("procgen-"):
            from procgen import ProcgenGym3Env

            self.package = "procgen"
            self.engine = ProcgenGym3Env(
                num=1,
                env_name=self.kind[8:],
                num_levels=1,
                start_level=seed,
                rand_seed=seed,
                distribution_mode="easy",
                num_threads=1,
            )
            # Gym3's noop is not necessarily index zero. Our deadline fallback is.
            combos = self.engine.combos
            self.mapping = [i for i, keys in enumerate(combos) if not keys]
            self.mapping += [i for i, keys in enumerate(combos) if keys]
            self.actions = ["wait"] + ["+".join(combos[i]) for i in self.mapping[1:]]
            _, obs, _ = self.engine.observe()
            self.image = obs["rgb"][0]
        elif self.kind == "crafter":
            import crafter

            class DeterministicCrafter(crafter.Env):
                def _balance_chunk(self, chunk, objects):
                    # Upstream stores chunk objects in a set. Default object
                    # hashes depend on memory addresses, changing which creature
                    # a seeded random despawn selects across fresh processes.
                    ordered = sorted(objects, key=lambda obj: tuple(int(v) for v in obj.pos))
                    return super()._balance_chunk(chunk, ordered)

            self.package = "crafter"
            self.engine = DeterministicCrafter(seed=seed, length=max_steps, size=(160, 160))
            self.image = self.engine.reset()
            self.mapping = list(range(self.engine.action_space.n))
            self.actions = list(self.engine.action_names)
        elif self.kind == "miniworld-oneroom":
            import gymnasium as gym
            import miniworld  # noqa: F401

            self.package = "miniworld"
            self.engine = gym.make(
                "MiniWorld-OneRoom-v0", render_mode="rgb_array", max_episode_steps=max_steps
            )
            self.image, _ = self.engine.reset(seed=seed)
            # The task has no noop. Wait advances one tick with zero movement via
            # an existing pickup action, which has no effect in this task.
            names = [a.name for a in self.engine.unwrapped.actions]
            self.mapping = [names.index("pickup"), 0, 1, 2]
            self.actions = ["wait", "turn_left", "turn_right", "move_forward"]
        elif self.kind in {"nethack-score", "minihack-room"}:
            import gymnasium as gym
            import nle  # noqa: F401
            from nle import nethack

            self.package = "nle" if self.kind == "nethack-score" else "minihack"
            actions = [
                nethack.MiscDirection.WAIT,
                *nethack.CompassDirection,
                nethack.MiscDirection.UP,
                nethack.MiscDirection.DOWN,
                nethack.MiscAction.MORE,
            ]
            if self.kind == "minihack-room":
                import minihack  # noqa: F401

                self.engine = gym.make(
                    "MiniHack-Room-5x5-v0",
                    actions=actions,
                    observation_keys=("tty_chars", "tty_colors"),
                    render_mode="pixel",
                    max_episode_steps=max_steps,
                )
            else:
                self.engine = gym.make(
                    "NetHackScore-v0",
                    actions=actions,
                    observation_keys=("tty_chars", "tty_colors"),
                    render_mode="pixel",
                    max_episode_steps=max_steps,
                    savedir=None,
                )
            self.engine.unwrapped.seed(core=seed, disp=seed, reseed=False)
            self.engine.reset(seed=seed)
            self.actions = [a.name.lower() for a in actions]
            self.mapping = list(range(len(actions)))
            self.image = self.engine.render().copy()
        elif self.kind == "cdda-first-weapon":
            if __package__:
                from .cdda_engine import CDDAPixelsEnv
            else:
                from cdda_engine import CDDAPixelsEnv

            self.package = "Cataclysm: Dark Days Ahead"
            self.engine = CDDAPixelsEnv(seed)
            self.actions = list(self.engine.actions)
            self.mapping = list(range(len(self.actions)))
            self.image = self.engine.reset()
        elif self.kind == "warzone-first-derrick":
            if __package__:
                from .warzone_engine import WarzonePixelsEnv
            else:
                from warzone_engine import WarzonePixelsEnv

            self.package = "Warzone 2100"
            self.engine = WarzonePixelsEnv(seed)
            self.actions = list(self.engine.actions)
            self.mapping = list(range(len(self.actions)))
            self.image = self.engine.reset()
        elif self.kind == "mindustry-copper":
            if __package__:
                from .mindustry_engine import MindustryPixelsEnv
            else:
                from mindustry_engine import MindustryPixelsEnv

            self.package = "Mindustry"
            self.engine = MindustryPixelsEnv(seed)
            self.actions = list(self.engine.actions)
            self.mapping = list(range(len(self.actions)))
            self.image = self.engine.reset()
        elif self.kind == "openttd-first-road":
            if __package__:
                from .openttd_engine import OpenTTDPixelsEnv
            else:
                from openttd_engine import OpenTTDPixelsEnv

            self.package = "OpenTTD"
            self.engine = OpenTTDPixelsEnv(seed)
            self.actions = list(self.engine.actions)
            self.mapping = list(range(len(self.actions)))
            self.image = self.engine.reset()
        elif self.kind == "dcss-first-experience":
            if __package__:
                from .crawl_engine import CrawlPixelsEnv
            else:
                from crawl_engine import CrawlPixelsEnv

            self.package = "DCSS"
            self.engine = CrawlPixelsEnv(seed)
            self.actions = list(self.engine.actions)
            self.mapping = list(range(len(self.actions)))
            self.image = self.engine.reset()
        elif self.kind == "supertux-first-coin":
            if __package__:
                from .supertux_engine import SuperTuxPixelsEnv
            else:
                from supertux_engine import SuperTuxPixelsEnv

            self.package = "SuperTux"
            self.engine = SuperTuxPixelsEnv(seed)
            self.actions = list(self.engine.actions)
            self.mapping = list(range(len(self.actions)))
            self.image = self.engine.reset()
        elif self.kind == "luanti-chop-tree":
            if __package__:
                from .craftium_engine import CraftiumPixelsEnv
            else:
                from craftium_engine import CraftiumPixelsEnv

            self.package = "craftium"
            self.engine = CraftiumPixelsEnv(seed, max_steps)
            self.actions = list(self.engine.actions)
            self.mapping = list(range(len(self.actions)))
            self.image = self.engine.reset()
        elif self.kind == "football-empty-goal":
            if __package__:
                from .football_engine import FootballPixelsEnv
            else:
                from football_engine import FootballPixelsEnv

            self.package = "gfootball"
            self.engine = FootballPixelsEnv(seed)
            self.actions = list(self.engine.actions)
            self.mapping = list(range(len(self.actions)))
            self.image = self.engine.reset()
        elif self.kind == "unity-food-collector":
            # This file is also launched directly by the legacy Python worker.
            if __package__:
                from .unity_engine import UnityPixelsEnv
            else:
                from unity_engine import UnityPixelsEnv

            self.package = "mlagents-envs"
            self.engine = UnityPixelsEnv(seed)
            self.actions = list(self.engine.actions)
            self.mapping = list(range(len(self.actions)))
            self.image = self.engine.reset()
        elif self.kind == "supertuxkart-lighthouse":
            import pystk2

            self.package = "PySuperTuxKart2"
            self.scratch = tempfile.TemporaryDirectory(prefix="ggbench-stk-")
            os.environ["SUPERTUXKART_SAVEDIR"] = self.scratch.name
            graphics = pystk2.GraphicsConfig.ld()
            graphics.display = False
            graphics.screen_width, graphics.screen_height = 320, 240
            pystk2.init(graphics)
            config = pystk2.RaceConfig(track="lighthouse", num_kart=1)
            config.seed, config.laps, config.step_size = seed, 1, 0.2
            config.players[0].controller = pystk2.PlayerConfig.Controller.PLAYER_CONTROL
            config.players[0].camera_mode = pystk2.PlayerConfig.CameraMode.ON
            self.engine = pystk2.Race(config)
            self.engine.start()
            self.state = pystk2.WorldState()
            self.track = pystk2.Track()
            self.track.update()
            for _ in range(100):
                self.engine.step(pystk2.Action())
                self.state.update()
                if self.state.phase in {
                    pystk2.WorldState.Phase.GO_PHASE,
                    pystk2.WorldState.Phase.RACE_PHASE,
                }:
                    break
            else:
                raise ValueError("Race failed to start")
            # Fixed neutral pre-roll lets the native starting camera/GUI settle.
            # This is part of task initialization, identical for every agent.
            for _ in range(50):
                self.engine.step(pystk2.Action())
            self.state.update()
            self.actions = [
                "wait",
                "accelerate",
                "accelerate_left",
                "accelerate_right",
                "brake",
                "rescue",
            ]
            self.mapping = list(range(len(self.actions)))
            self.image = self.engine.render_data[0].image.copy()
        elif self.kind == "pettingzoo-pistonball":
            from pettingzoo.butterfly import pistonball_v6

            self.package = "pettingzoo"
            self.engine = pistonball_v6.parallel_env(
                n_pistons=5,
                continuous=False,
                random_drop=True,
                random_rotate=True,
                max_cycles=max_steps,
                render_mode="rgb_array",
            )
            observations, _ = self.engine.reset(seed=seed)
            self.player = "piston_2"
            self.image = observations[self.player]
            self.actions = ["wait", "piston_down", "piston_up"]
            self.mapping = [1, 0, 2]
        elif self.kind == "atari-breakout":
            import ale_py

            self.package = "ale-py"
            self.engine = ale_py.ALEInterface()
            self.engine.setInt("random_seed", seed)
            self.engine.setFloat("repeat_action_probability", 0.0)
            self.engine.setInt("frame_skip", 4)
            from ale_py import roms

            self.engine.loadROM(roms.get_rom_path("breakout"))
            self.mapping = list(self.engine.getMinimalActionSet())
            self.actions = [x.name.lower() for x in self.mapping]
            if self.actions[0] != "noop":
                raise ValueError("Atari action zero must be NOOP")
            self.image = self.engine.getScreenRGB()
        elif self.kind == "retro-airstriker":
            import stable_retro as retro

            self.package = "stable-retro"
            self.engine = retro.make(
                game="Airstriker-Genesis-v0",
                inttype=retro.data.Integrations.STABLE,
                render_mode="rgb_array",
            )
            self.image, _ = self.engine.reset(seed=seed)
            self.mapping = [np.zeros(len(self.engine.buttons), dtype=np.int8)]
            self.actions = ["wait"]
            for button in ["LEFT", "RIGHT", "UP", "DOWN", "A", "B", "C", "START"]:
                if button in self.engine.buttons:
                    mask = np.zeros(len(self.engine.buttons), dtype=np.int8)
                    mask[self.engine.buttons.index(button)] = 1
                    self.mapping.append(mask)
                    self.actions.append(button.lower())
        else:
            raise ValueError("Unknown task")
        self.metadata = {
            "task_id": task["id"],
            "task_version": task["task_version"],
            "engine": self.package,
            "engine_version": (
                self.engine.engine_version
                if hasattr(self.engine, "engine_version")
                else importlib.metadata.version(self.package)
            ),
            "numpy_version": np.__version__,
            "observation": "rendered-rgb-only",
            "score_range": task["score_range"],
            "seed_policy": "fixed-initial-reset",
            "simulation": "lockstep",
            "replay": "exact-frame-and-score",
        }
        if self.kind == "unity-food-collector":
            self.metadata.update(
                assets_sha256=self.engine.assets_sha256,
                scene="VisualFoodCollector",
                controlled_agent="lowest-initial-agent-id",
                peer_policy="no-op",
                capture_frame_rate=30,
                camera_size=[84, 84],
                reward_definition="sum of native food rewards; green +1, red -1",
            )
        elif self.kind == "cdda-first-weapon":
            self.metadata.update(
                scenario="native tutorial; first wielded baseball bat",
                camera_size=[960, 640],
                renderer="native SDL2 software / UltimateCataclysm tiles",
                control_policy="one native key per decision; tutorial popups remain visible",
                reward_definition="one when the native avatar wields the tutorial baseball bat",
                initialization="native tutorial world and preset character; fresh user directory",
            )
        elif self.kind == "warzone-first-derrick":
            self.metadata.update(
                scenario="native TUTORIAL3; first constructed oil derrick",
                camera_size=[960, 640],
                renderer="native SDL3/OpenGL / Xvfb / Mesa",
                cursor_step_pixels=32,
                fine_cursor_step_pixels=8,
                step_milliseconds=100,
                initialization="40 native frames; fresh tutorial and settings",
                reward_definition="one on first native completed structure; two unit losses end task",
            )
        elif self.kind == "mindustry-copper":
            self.metadata.update(
                scenario="serpulo/groundZero; native first-15-copper tutorial objective",
                camera_size=[960, 640],
                renderer="native SDL/OpenGL / Xvfb / Mesa",
                initialization="120 native frames; fresh player and settings",
                cursor_step_pixels=32,
                frames_per_action=6,
                physics_step_seconds=1 / 60,
                optional_effects=False,
                reward_definition="native player-plus-core copper gain from initial total; target 15",
            )
        elif self.kind == "openttd-first-road":
            self.metadata.update(
                scenario="new 64x64 company in 1950; first owned road",
                camera_size=[800, 600],
                renderer="native 32bpp software framebuffer; OpenGFX 7.1",
                cursor_step_pixels=32,
                step_milliseconds=30,
                initialization="16 native ticks; fresh company and configuration",
                reward_definition="one when native company infrastructure owns at least two road bits",
            )
        elif self.kind == "dcss-first-experience":
            self.metadata.update(
                scenario="Dungeon:1; Minotaur Fighter with war axe; first experience",
                camera_size=[800, 600],
                renderer="native SDL2 tiles / Mesa",
                control_policy="one native key per decision; no auto-explore or auto-fight",
                reward_definition="one on first native experience gain; death ends task",
                seed_policy="native uint64 seed; benchmark zero maps to uint64 maximum",
                initialization="advance title and seed-confirmation menus before observing",
            )
        elif self.kind == "supertux-first-coin":
            self.metadata.update(
                level="world1/welcome_antarctica.stl",
                camera_size=[640, 480],
                renderer="SDL software",
                frames_per_action=8,
                physics_step_seconds=0.015,
                reward_definition="native level coin count; first coin completes task",
                initialization="skip level-introduction menu and fades; fresh player/save",
            )
        elif self.kind == "luanti-chop-tree":
            self.metadata.update(
                scenario="Craftium/ChopTree-v0: first tree block",
                camera_size=[64, 64],
                step_seconds=0.02,
                seed_policy="pinned world snapshot; fixed map/Lua seed on initial reset",
                engine_variant="serial-lockstep-v2",
                weather="disabled via upstream enable_weather setting",
                mesh_generation_threads=1,
                reward_definition="native Lua tree-node dig reward; first reward completes task",
            )
        elif self.kind == "football-empty-goal":
            self.metadata.update(
                scenario="academy_empty_goal_close",
                camera_size=[320, 180],
                control_policy="release movement and shot before each decision",
                reward_definition="native goal reward, no checkpoint shaping",
            )
        elif self.kind == "supertuxkart-lighthouse":
            self.metadata.update(
                track="lighthouse",
                step_seconds=0.2,
                neutral_preroll_steps=50,
                renderer="Mesa software / deterministic-render-v1",
                camera_size=[int(self.image.shape[1]), int(self.image.shape[0])],
                reward_definition="max(0, native overall distance) / native track length",
            )

    def frame(self):
        image = np.asarray(self.image)
        if image.ndim != 3 or image.shape[2] not in (3, 4) or image.dtype != np.uint8:
            raise ValueError("Engine did not provide RGB pixels")
        out = io.BytesIO()
        Image.fromarray(image).convert("RGB").save(out, format="PNG")
        return base64.b64encode(out.getvalue()).decode()

    def step(self, action):
        if type(action) is not int or not 0 <= action < len(self.actions) or self.done:
            raise ValueError("Invalid action or finished episode")
        value = self.mapping[action]
        if self.kind.startswith("procgen-"):
            self.engine.act(np.array([value], dtype=np.int32))
            reward, obs, first = self.engine.observe()
            self.raw += float(reward[0])
            # Gym3 auto-resets. Stop immediately on first=True: never score or
            # expose a frame from the next episode as part of this episode.
            self.done = bool(first[0])
            if not self.done:
                self.image = obs["rgb"][0]
        elif self.kind == "crafter":
            self.image, reward, self.done, info = self.engine.step(value)
            achievements = {k: int(v) for k, v in info["achievements"].items()}
            self.raw = float(sum(v > 0 for v in achievements.values()))
            self.metrics = {
                "achievements": achievements,
                "score_definition": "unique achievements / 22; not Crafter geometric-mean success metric",
            }
        elif self.kind == "supertuxkart-lighthouse":
            import pystk2

            control = pystk2.Action()
            control.acceleration = 1.0 if value in (1, 2, 3) else 0.0
            control.steer = -0.5 if value == 2 else 0.5 if value == 3 else 0.0
            control.brake = value == 4
            control.rescue = value == 5
            self.engine.step(control)
            self.state.update()
            kart = self.state.players[0].kart
            # Before the first physics tick the engine reports -one track length.
            # Subtracting that sentinel would award a lap for crossing the start.
            distance = max(0.0, float(kart.overall_distance))
            self.raw = distance / float(self.track.length)
            self.metrics = {
                "distance_m": distance,
                "track_length_m": float(self.track.length),
                "finished": bool(kart.has_finished_race),
                "asset_version": "1.5",
            }
            self.image = self.engine.render_data[0].image.copy()
            self.done = bool(kart.has_finished_race)
        elif self.kind == "pettingzoo-pistonball":
            actions = {p: (2 if (self.t // 4) % 2 == 0 else 0) for p in self.engine.agents}
            actions[self.player] = value
            observations, rewards, terminated, truncated, _ = self.engine.step(actions)
            self.raw += float(rewards[self.player])
            self.image = observations[self.player]
            self.done = bool(terminated[self.player] or truncated[self.player])
        elif self.kind == "atari-breakout":
            self.raw += float(self.engine.act(value))
            self.image = self.engine.getScreenRGB()
            self.done = self.engine.game_over()
        elif self.kind in {"nethack-score", "minihack-room"}:
            _, reward, terminated, truncated, _ = self.engine.step(value)
            self.raw += float(reward)
            self.image = self.engine.render().copy()
            self.done = bool(terminated or truncated)
        else:
            self.image, reward, terminated, truncated, _ = self.engine.step(value)
            self.raw += float(reward)
            self.done = bool(terminated or truncated)
        self.t += 1
        self.done = bool(self.done or self.t >= self.max_steps)

    def result(self):
        lo, hi = self.task["score_range"]
        return {
            "raw_score": self.raw,
            "score": max(0.0, min(1.0, (self.raw - lo) / (hi - lo))),
            "steps": self.t,
            "metrics": {"normalization": [lo, hi], **self.metrics},
        }

    def close(self):
        if self.kind == "supertuxkart-lighthouse" and self.engine is not None:
            import pystk2

            self.engine.stop()
            self.engine = None
            pystk2.clean()
            self.scratch.cleanup()
        if hasattr(self.engine, "close"):
            self.engine.close()


def main():
    # Linux Python workers use a separate reply pipe. Other workers use stdout.
    # Send native library output to stderr before loading an engine.
    descriptor = os.environ.pop("GGBENCH_WORKER_REPLY_FD", None)
    reply_fd = int(descriptor) if descriptor is not None else os.dup(sys.stdout.fileno())
    os.set_inheritable(reply_fd, False)
    output = os.fdopen(reply_fd, "w", buffering=1)
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    env = None
    try:
        for line in sys.stdin:
            try:
                request = json.loads(line)
                command = request["command"]
                with contextlib.redirect_stdout(sys.stderr):
                    if command == "init":
                        env = Environment(request["task"], request["seed"], request["max_steps"])
                        result = {
                            "actions": env.actions,
                            "instructions": env.instructions,
                            "metadata": env.metadata,
                        }
                    elif env is None:
                        raise ValueError("Initialize the engine first")
                    elif command == "frame":
                        result = {"png": env.frame()}
                    elif command == "step":
                        env.step(request["action"])
                        result = {"done": env.done}
                    elif command == "result":
                        result = env.result()
                    elif command == "close":
                        output.write(json.dumps({"closed": True}) + "\n")
                        break
                    else:
                        raise ValueError("Unknown worker command")
                output.write(json.dumps(result, allow_nan=False) + "\n")
            except Exception as exc:
                traceback.print_exc(file=sys.stderr)
                output.write(json.dumps({"error": f"{type(exc).__name__}: {exc}"}) + "\n")
                break
    finally:
        if env is not None:
            env.close()


if __name__ == "__main__":
    main()
