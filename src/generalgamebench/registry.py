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
            task_version="2",
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
        "unity-food-collector": Task(
            "unity-food-collector",
            "unity-ml-agents-environments",
            "unity",
            "Collect green food and avoid red food in the 3D arena. Control one agent; peers wait. Forward, strafe and turn navigate; fire emits a beam. Score is net food reward divided by ten.",
            (0, 10),
        ),
        "football-empty-goal": Task(
            "football-empty-goal",
            "google-research-football",
            "docker-football",
            "Score a goal in Football Academy's close-range scenario. Move in eight directions or shoot. Each control is released before the next decision. Score is the native goal reward.",
            (0, 1),
        ),
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


TASKS.update(
    {
        "supertuxkart-lighthouse": Task(
            "supertuxkart-lighthouse",
            "supertuxkart",
            "docker-stk",
            "Drive one lap of the Lighthouse track. Accelerate and steer to stay on the road. Each action advances 0.2 seconds. Score is forward progress as a fraction of one lap.",
            (0, 1),
            task_version="2",
        )
    }
)

TASKS.update(
    {
        "luanti-chop-tree": Task(
            "luanti-chop-tree",
            "luanti",
            "docker-craftium",
            "Find and chop one tree block in the pinned snowy forest. You start with a steel axe. Move, jump, look and dig. Only digging a tree node earns a reward; the first one completes this task.",
            (0, 1),
        )
    }
)

EXPERIMENTAL_TASKS = {}

TASKS["supertux-first-coin"] = Task(
    "supertux-first-coin",
    "supertux",
    "docker-supertux",
    "Collect one coin in Welcome to Antarctica. Move and jump; run makes movement faster. Hit question blocks from below or touch visible coins. The first coin completes the task; death ends it.",
    (0, 1),
)


def task_dict(task_id):
    return asdict((TASKS | EXPERIMENTAL_TASKS)[task_id])


TASKS["dcss-first-experience"] = Task(
    "dcss-first-experience",
    "dungeon-crawl-stone-soup",
    "docker-crawl",
    "Explore Dungeon Crawl Stone Soup as a Minotaur Fighter and earn your first experience by defeating a monster. Compass directions move or attack adjacent enemies. Wait passes one turn; confirm and cancel answer native prompts. The first experience gain completes the task; death ends it.",
    (0, 1),
)

TASKS["openttd-first-road"] = Task(
    "openttd-first-road",
    "openttd",
    "docker-openttd",
    "Build a road in a new OpenTTD company. Open the road toolbar, select autoroad, then press, drag and release on suitable land. Cursor directions move 32 screen pixels; the cursor begins at the center. Native company ownership of at least two road bits completes the task. This introductory construction task does not score transport profit.",
    (0, 1),
)

TASKS["mindustry-copper"] = Task(
    "mindustry-copper",
    "mindustry",
    "docker-mindustry",
    "Mine 15 copper in Mindustry's native Ground Zero tutorial map. Move near orange copper ore, aim the pointer and click once to start mining. Wait lets mining continue. The pointer begins at screen center and moves 32 pixels per cursor action; the game shows hovered terrain in its native HUD. Movement controls hold WASD for six frames and then release. Score is copper gained in the player inventory and core divided by 15; player death ends the task.",
    (0, 15),
)

TASKS["cdda-first-weapon"] = Task(
    "cdda-first-weapon",
    "cataclysm-dark-days-ahead",
    "docker-cdda",
    "Find and wield the baseball bat in Cataclysm: Dark Days Ahead's native tutorial. Compass directions move and open doors. Dismiss advances tutorial popups; wield opens the native item menu and numbered choices select its entries. Confirm and cancel answer prompts. Wielding the bat completes this introductory task; death ends it.",
    (0, 1),
)

TASKS["warzone-first-derrick"] = Task(
    "warzone-first-derrick",
    "warzone-2100",
    "docker-warzone",
    "Construct the first oil derrick in Warzone 2100's native tutorial. Select a construction truck with a left click, then left click an oil resource to build. Follow the game's tutorial messages. The pointer starts at screen center; cursor actions move 32 pixels and fine cursor actions move 8. Wait advances construction by 100 milliseconds. The first completed structure wins; losing both trucks ends the task.",
    (0, 1),
)
