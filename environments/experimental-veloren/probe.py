import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

out = Path("/out")
tag = os.environ.get("TAG", "first")
scratch = Path("/tmp") / tag
scratch.mkdir()
log = open(out / f"veloren-{tag}.log", "w")
p = subprocess.Popen(
    ["xvfb-run", "-a", "-s", "-screen 0 960x640x24", "/engine/veloren-voxygen"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=log,
    text=True,
    env={
        **os.environ,
        "VELOREN_USERDATA": str(scratch / "userdata"),
        "HOME": str(scratch),
        "XDG_RUNTIME_DIR": "/tmp",
        "GGBENCH_CAPTURE": str(scratch / "camera.png"),
        "GGBENCH_SEED": "71",
    },
)
actions = json.loads(os.environ.get("ACTIONS", "[]"))
records = []
try:
    for step in range(len(actions) + 1):
        while True:
            line = p.stdout.readline()
            if not line:
                raise RuntimeError("game exited")
            if line.startswith("GGBENCH "):
                break
            log.write(line)
            log.flush()
        state = json.loads(line[8:])
        blob = (scratch / "camera.png").read_bytes()
        (out / f"veloren-{tag}-{step}.png").write_bytes(blob)
        state["hash"] = hashlib.sha256(blob).hexdigest()
        records.append(state)
        print(step, state, flush=True)
        if step == len(actions) or state["collected"] > 0:
            break
        time.sleep(float(os.environ.get("DELAY", "0")))
        p.stdin.write(str(actions[step]) + "\n")
        p.stdin.flush()
finally:
    p.stdin.close()
    try:
        p.wait(5)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
    (out / f"veloren-{tag}.json").write_text(json.dumps(records))
