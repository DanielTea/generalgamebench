import json
import subprocess
import sys

suite = [
    "coin-run",
    "dodge-lanes",
    "doom-basic",
    "doom-defend-center",
    "doom-defend-line",
    "doom-take-cover",
    "doom-health",
    "doom-corridor",
    "doom-home",
    "doom-predict",
]
for agent in ["idle", "random", "react", "tracker"]:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "screenquest_arena.cli",
            "run",
            "--agent",
            agent,
            "--games",
            *suite,
            "--seeds",
            "10",
            "--steps",
            "80",
            "--output",
            "runs/baselines-final",
        ],
        check=True,
    )
print(json.dumps({"completed": True, "episodes": 400}))
