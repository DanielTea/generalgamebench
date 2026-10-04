"""A stateless discrete controller and native camera for Football Academy."""


class FootballPixelsEnv:
    actions = [
        "wait",
        "left",
        "up_left",
        "up",
        "up_right",
        "right",
        "down_right",
        "down",
        "down_left",
        "shoot",
    ]
    mapping = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12]

    def __init__(self, seed):
        import gfootball.env as football
        from gfootball.env import football_action_set

        self.controls = football_action_set
        self.env = football.create_environment(
            env_name="academy_empty_goal_close",
            representation="pixels",
            rewards="scoring",
            render=True,
            stacked=False,
            channel_dimensions=(320, 180),
            write_goal_dumps=False,
            write_full_episode_dumps=False,
            other_config_options={
                "game_engine_random_seed": seed,
                "render_resolution_x": 320,
            },
        )
        self.done = False

    def reset(self):
        return self.env.reset()

    def step(self, action):
        if self.done or type(action) is not int or not 0 <= action < len(self.actions):
            raise ValueError("Illegal Football action or finished episode")
        # Release held controls without advancing physics. Wait is neutral even
        # after a movement/shot, including when used as a late-action fallback.
        engine = self.env.unwrapped._env._env
        for release in (self.controls.action_release_direction, self.controls.action_release_shot):
            engine.perform_action(release._backend_action, True, 0)
        image, reward, self.done, _ = self.env.step(self.mapping[action])
        return image, float(reward), self.done, False, {}

    def close(self):
        self.env.close()
