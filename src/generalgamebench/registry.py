"""Versioned tasks, separate from catalog families and installation availability."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Task:
    id: str
    family: str
    runtime: str
    objective: str
    score_range: tuple[float, float]
    task_version: str = "1"


# Frozen task-v1 normalization ranges, not fitted to our agents' scores.
# Always retain raw rewards; short exhibitions are not full Procgen evaluations.
PROCGEN_RANGES = {
    "bigfish": (1, 40),
    "bossfight": (0.5, 13),
    "caveflyer": (2, 12),
    "chaser": (0.5, 13),
    "climber": (1, 12.6),
    "coinrun": (5, 10),
    "dodgeball": (1.5, 19),
    "fruitbot": (-1.5, 32.4),
    "heist": (3.5, 10),
    "jumper": (3, 10),
    "leaper": (3, 10),
    "maze": (5, 10),
    "miner": (1.5, 13),
    "ninja": (3.5, 10),
    "plunder": (4.5, 30),
    "starpilot": (2.5, 64),
}
PROCGEN_OBJECTIVES = {
    "bigfish": "Eat smaller fish and avoid larger fish. Move in four directions.",
    "bossfight": "Dodge enemy projectiles and shoot the boss. D fires.",
    "caveflyer": "Fly through the cave to the exit without hitting walls. D fires.",
    "chaser": "Collect green orbs and avoid chasing enemies.",
    "climber": "Climb platforms and collect stars; up jumps.",
    "coinrun": "Reach the coin at the end of the platform level; up jumps.",
    "dodgeball": "Avoid enemy balls and defeat enemies; D throws a ball.",
    "fruitbot": "Collect fruit while avoiding obstacles and non-fruit objects; D fires.",
    "heist": "Collect keys to open matching doors and reach the gem.",
    "jumper": "Jump across platforms to the carrot; up jumps.",
    "leaper": "Cross roads and water to reach the finish without being hit.",
    "maze": "Navigate the maze to the cheese using four-direction movement.",
    "miner": "Collect diamonds, avoid falling rocks, and reach the exit.",
    "ninja": "Reach the mushroom; hold up to charge a jump and release to jump.",
    "plunder": "Shoot enemy pirate ships and avoid friendly ships; D fires.",
    "starpilot": "Fly, dodge hazards and shoot enemies; D fires.",
}
TASKS = {
    f"procgen-{name}": Task(
        f"procgen-{name}", f"procgen-{name}", "procgen", objective, PROCGEN_RANGES[name]
    )
    for name, objective in PROCGEN_OBJECTIVES.items()
}
TASKS.update(
    {
        "crafter": Task(
            "crafter",
            "crafter",
            "research",
            "Survive, collect resources, craft tools and unlock achievements.",
            (0, 22),
        ),
        "miniworld-oneroom": Task(
            "miniworld-oneroom",
            "miniworld",
            "research",
            "Navigate the first-person room and touch the red box.",
            (0, 1),
        ),
        "pettingzoo-pistonball": Task(
            "pettingzoo-pistonball",
            "pettingzoo-environments",
            "research",
            "Move the ball left. Control the middle piston; the other pistons follow a fixed periodic policy.",
            (-100, 100),
        ),
        "atari-breakout": Task(
            "atari-breakout",
            "atari-arcade-learning-environment",
            "research",
            "Move the paddle and break bricks. Fire starts the ball.",
            (0, 864),
        ),
        "retro-airstriker": Task(
            "retro-airstriker",
            "stable-retro-library",
            "research",
            "Pilot the ship, dodge enemies and shoot. This is the freely distributed Airstriker Genesis demo.",
            (0, 10000),
        ),
    }
)

TASKS.update(
    {
        "nethack-score": Task(
            "nethack-score",
            "nethack",
            "roguelike",
            "Explore NetHack as the player character, survive and gain game score. Compass actions move or attack. The image is the game's native tile renderer.",
            (0, 1000),
        ),
        "minihack-room": Task(
            "minihack-room",
            "minihack",
            "roguelike",
            "Navigate the small room to the staircase. Use compass directions; the goal gives reward one.",
            (0, 1),
        ),
    }
)


EXPERIMENTAL_TASKS = {
    "supertuxkart-lighthouse": Task(
        "supertuxkart-lighthouse",
        "supertuxkart",
        "research",
        "Drive one lap of the Lighthouse track. Accelerate and steer to stay on the road. Each action advances 0.2 seconds. Score is forward progress as a fraction of one lap.",
        (0, 1),
    )
}


def task_dict(task_id):
    return asdict((TASKS | EXPERIMENTAL_TASKS)[task_id])
