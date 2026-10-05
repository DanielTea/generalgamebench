# Writing

Use ASD-STE100 for new user-facing text, documentation and task replies.
Use short sentences, active voice and consistent technical terms.
Keep required API names, metadata tags and source identifiers exact.

# Leaderboard latency

Use suite p95 below 200 ms. Exactly 200 ms fails.
Pool all recorded response times from the complete suite. Use linear interpolation.
Keep scores, error counts and trust status separate from this latency test.
Keep historical evidence unchanged. State its original recording rules.
