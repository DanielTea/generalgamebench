# Roadmap

The [public GitHub project](https://github.com/users/DanielTea/projects/4) tracks the work.

Shipped: portable evaluation package, two original 2D games, eight ViZDoom scenarios, four local policies, real Astra/Claude exhibition, suite p95 limit below 200 ms, evidence replay, uncertainty intervals, tests, static public leaderboard and submission form.

Next milestones:

1. [Independent isolated workers and signed admission](https://github.com/DanielTea/generalgamebench/issues/1).
2. [Modern 3D adapters](https://github.com/DanielTea/generalgamebench/issues/2), extending the validated SuperTuxKart and Luanti tasks.
3. [Licensed commercial-game hosts](https://github.com/DanielTea/generalgamebench/issues/3), with separate task validation per game.
4. [Longer, statistically stronger model evaluations](https://github.com/DanielTea/generalgamebench/issues/4).
5. [Continuous realtime capture and input acknowledgement](https://github.com/DanielTea/generalgamebench/issues/5).

The public reference suite is ready for local experimentation. The production adversarial competition service and modern AAA coverage are not yet implemented.

## Expanded Mac implementation

33 optional tasks now pass local deterministic replay. The suite covers 43 scenarios across 36 of 45 catalog cards, adding ten of the previously unfinished integrations. Three native candidates still fail admission (0 A.D., StarCraft II and Veloren), and six game families lack usable local installations. The 5 October hosted-model refresh uses all 43 scenarios; the archived model standings retain their original 33-task cohort. Longer horizons and more seeds remain necessary for reliable skill comparisons. See the [coverage matrix and blockers](GAMES.md).

Hugging Face is a planned second distribution channel: a static Space displays a pinned snapshot from a separate versioned Dataset. The tested local export preserves task/model revisions, exact seed sets, suite identity and trust labels. Evaluation workers, credentials and submission execution stay outside the Space. No Hugging Face repository has been created or published yet.
