"""Optional transport wrapper; not certified isolation. Build only trusted Dockerfiles."""

import os
import re
import sys

if len(sys.argv) != 2 or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._/@:-]*", sys.argv[1]):
    raise SystemExit("Usage: container-agent.py IMAGE (pin an image digest for reproducibility)")
os.execvp(
    "docker",
    [
        "docker",
        "run",
        "--rm",
        "-i",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=64",
        "--memory=512m",
        "--cpus=1",
        "--user=65534:65534",
        "--ipc=none",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=32m",
        sys.argv[1],
    ],
)
