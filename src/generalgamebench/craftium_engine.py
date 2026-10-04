"""Native Luanti camera and one-tree objective; structured state stays private."""

import tempfile


class CraftiumPixelsEnv:
    actions = ["wait", "forward", "jump", "dig", "look_right", "look_left", "look_up", "look_down"]

    def __init__(self, seed, max_steps):
        import craftium  # noqa: F401 -- registers the official Gymnasium task
        import gymnasium as gym

        self.scratch = tempfile.TemporaryDirectory(prefix="ggbench-luanti-")
        self.env = None
        self.done = False
        try:
            self.env = gym.make(
                "Craftium/ChopTree-v0",
                seed=seed,
                max_timesteps=max_steps,
                frameskip=1,
                sync_mode=True,
                offscreen_sdl=True,
                enable_voxel_obs=False,
                run_dir_prefix=self.scratch.name,
                minetest_conf={"mesh_generation_threads": 1, "enable_weather": False},
            )
            if self.env.action_space.n != len(self.actions):
                raise ValueError("Unexpected Craftium control mapping")
            self.initial, _ = self.env.reset(seed=seed)
        except BaseException:
            self.close()
            raise

    def reset(self):
        return self.initial.copy()

    def step(self, action):
        if self.done or type(action) is not int or not 0 <= action < len(self.actions):
            raise ValueError("Illegal Luanti action or finished episode")
        image, reward, terminated, truncated, _ = self.env.step(action)
        # The upstream Lua referee rewards a dug tree node. This bounded task
        # ends at its first such reward; upstream death also ends the episode.
        self.done = bool(terminated or truncated or reward >= 1)
        return image, float(reward), self.done, False, {}

    def close(self):
        try:
            if self.env is not None:
                self.env.close()
                self.env = None
        finally:
            self.scratch.cleanup()
