# Roadmap

The [public GitHub project](https://github.com/users/DanielTea/projects/4) tracks the work.

Shipped: portable evaluation package, two original 2D games, eight ViZDoom scenarios, four local policies, real Astra/Claude exhibition, strict measured deadline gate, evidence replay, uncertainty intervals, tests, static public leaderboard and submission form.

Next milestones:

1. [Independent isolated workers and signed admission](https://github.com/DanielTea/generalgamebench/issues/1).
2. [Modern 3D adapters](https://github.com/DanielTea/generalgamebench/issues/2), starting with SuperTuxKart and Luanti.
3. [Licensed commercial-game hosts](https://github.com/DanielTea/generalgamebench/issues/3), with separate task validation per game.
4. [Longer, statistically stronger model evaluations](https://github.com/DanielTea/generalgamebench/issues/4).
5. [Continuous realtime capture and input acknowledgement](https://github.com/DanielTea/generalgamebench/issues/5).

The public reference suite is ready for local experimentation. The production adversarial competition service and modern AAA coverage are not yet implemented.

## Expanded Mac implementation

23 additional optional tasks now pass local deterministic replay: 16 Procgen games plus Crafter, MiniWorld, Pistonball, Breakout, Airstriker, NetHack and MiniHack. The suite now covers 33 scenarios across 26 of the 45 catalog cards. SuperTuxKart launches but fails exact screenshot replay; the other 18 unadmitted cards still need their specific implementations and/or installations. See the current [coverage matrix](GAMES.md), not the older milestone text, for scope.

Hugging Face is a planned second distribution channel: a static Space displays a pinned snapshot from a separate versioned Dataset. The tested local export preserves task/model revisions, exact seed sets, suite identity and trust labels. Evaluation workers, credentials and submission execution stay outside the Space. No Hugging Face repository has been created or published yet.
