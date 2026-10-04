"""Smallest participant: a seeded random policy, no third-party dependencies."""

import json
import random
import sys

rng = random.Random(7)
print(json.dumps({"ready": True}), flush=True)
for line in sys.stdin:
    obs = json.loads(line)
    action = rng.randrange(len(obs["actions"]))
    print(json.dumps({"nonce": obs["nonce"], "action": action}), flush=True)
