"""Named submission suites. Never silently change a published suite definition."""

from dataclasses import asdict, dataclass

from .evidence import canonical, digest
from .games import DOOM, NATIVE
from .registry import TASKS


@dataclass(frozen=True)
class Suite:
    id: str
    description: str
    games: tuple[str, ...]
    seeds: tuple[int, ...] = (1000, 1001, 1002, 1003, 1004)
    max_steps: int = 80

    def definition(self):
        value = asdict(self)
        value["games"] = list(self.games)
        value["seeds"] = list(self.seeds)
        value["task_versions"] = {
            game: TASKS[game].task_version if game in TASKS else "1" for game in self.games
        }
        return value

    @property
    def sha256(self):
        return digest(canonical(self.definition()))


# The extended suite intentionally lists its members, rather than admitting
# future registry additions without a new suite ID.
EXTENDED_GAMES = (
    *NATIVE,
    *DOOM,
    "procgen-bigfish",
    "procgen-bossfight",
    "procgen-caveflyer",
    "procgen-chaser",
    "procgen-climber",
    "procgen-coinrun",
    "procgen-dodgeball",
    "procgen-fruitbot",
    "procgen-heist",
    "procgen-jumper",
    "procgen-leaper",
    "procgen-maze",
    "procgen-miner",
    "procgen-ninja",
    "procgen-plunder",
    "procgen-starpilot",
    "crafter",
    "miniworld-oneroom",
    "pettingzoo-pistonball",
    "atari-breakout",
    "retro-airstriker",
    "nethack-score",
    "minihack-room",
    "unity-food-collector",
    "football-empty-goal",
    "supertuxkart-lighthouse",
    "luanti-chop-tree",
    "supertux-first-coin",
    "dcss-first-experience",
    "openttd-first-road",
    "mindustry-copper",
    "cdda-first-weapon",
    "warzone-first-derrick",
)

SUITES = {
    "starter-v1": Suite("starter-v1", "Two bundled 2D games; quick integration check.", NATIVE),
    "portable-v1": Suite(
        "portable-v1", "Two bundled 2D games and eight native ViZDoom scenarios.", (*NATIVE, *DOOM)
    ),
    "extended-v1": Suite(
        "extended-v1", "All 43 admitted scenarios; additional runtimes required.", EXTENDED_GAMES
    ),
}
