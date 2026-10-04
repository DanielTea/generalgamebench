import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from PIL import Image

out = Path("/out")
tag = os.environ.get("TAG", "first")
scratch = Path("/tmp") / tag
scratch.mkdir()
log = open(out / f"0ad-{tag}.log", "w")
p = subprocess.Popen(
    [
        "xvfb-run",
        "-a",
        "-s",
        "-screen 0 960x640x24",
        "/source/binaries/system/pyrogenesis",
        "-autostart=random/mainland",
        "-autostart-seed=" + os.environ.get("SEED", "71"),
        "-autostart-aiseed=" + os.environ.get("SEED", "71"),
        "-autostart-player=1",
        "-autostart-civ=1:athen",
        "-autostart-civ=2:brit",
        "-autostart-biome=generic/temperate",
        "-autostart-placement=circle",
        "-autostart-size=128",
        "-autostart-players=2",
        "-autostart-victory=endless",
        "-fixed-frame-frequency=50",
        "-xres=960",
        "-yres=640",
        "-conf=gpuskinning:false",
        "-conf=postproc:false",
        "-conf=windowed:true",
        "-conf=shadows:false",
        "-conf=particles:false",
        "-conf=watereffects:false",
        "-conf=waterreflection:false",
        "-conf=waterrefraction:false",
        "-conf=rendererbackend:" + os.environ.get("BACKEND", "gl"),
        "-nosound",
        "-quickstart",
        "-mod=public",
    ],
    cwd="/source/binaries/system",
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=log,
    text=True,
    env={
        **os.environ,
        "HOME": str(scratch),
        "GGBENCH_CAPTURE": str(scratch / "camera.ppm"),
        "GGBENCH_SEED": os.environ.get("SEED", "71"),
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
        im = Image.open(scratch / "camera.ppm").convert("RGB")
        im.save(out / f"0ad-{tag}-{step}.png")
        state["hash"] = hashlib.sha256(im.tobytes()).hexdigest()
        records.append(state)
        print(step, state, flush=True)
        if step == len(actions) or state["wood"] >= 10:
            break
        time.sleep(float(os.environ.get("DELAY", "0")))
        p.stdin.write(str(actions[step]) + "\n")
        p.stdin.flush()
finally:
    p.terminate()
    try:
        p.wait(3)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
    (out / f"0ad-{tag}.json").write_text(json.dumps(records))
