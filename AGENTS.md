# Writing

Use ASD-STE100 for new user-facing text, documentation and task replies.
Use short sentences, active voice and consistent technical terms.
Keep required API names, metadata tags and source identifiers exact.

# Leaderboard scoring

Use the versioned 70% quality / 30% speed geometric score in weighted_score.py.
Use 1000 ms as the fixed latency reference. There is no hard latency limit.
Pool all recorded response times from the complete suite. Use linear interpolation.
Show quality, suite p95, errors and trust status separately from the weighted score.
Keep historical evidence unchanged. State its original recording rules.
Keep old latency flags only for evidence compatibility, never as current admission rules.
