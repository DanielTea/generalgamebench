"""Diagnostic only: native RGB/control/score works; exact pixel replay is not admitted.

Run inside the documented Linux x86_64 container with /assets read-only and /out
writable. TAG selects output names, ACTIONS is a JSON array, DELAY adds artificial
latency. This is not connected to the ranking registry.
"""

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import websocket
from PIL import Image
from s2clientprotocol import common_pb2 as common
from s2clientprotocol import sc2api_pb2 as sc

root = Path("/assets")
out = Path("/out")
tag = os.environ.get("TAG", "first")
scratch = Path("/tmp") / tag
scratch.mkdir()
log = open(out / f"sc2-{tag}.log", "w")
records = []
binary = root / "Versions/Base75689/SC2_x64"
p = subprocess.Popen(
    [
        str(binary),
        "-listen",
        "127.0.0.1",
        "-port",
        "5000",
        "-dataDir",
        str(root),
        "-tempDir",
        str(scratch),
        "-osmesapath",
        "/usr/lib/x86_64-linux-gnu/libOSMesa.so.8",
        "-displayMode",
        "0",
    ],
    cwd=str(root),
    stdout=log,
    stderr=log,
    env={
        **os.environ,
        "HOME": str(scratch),
    },
)
ws = None
serial = 0
try:
    for _ in range(600):
        if p.poll() is not None:
            raise RuntimeError("SC2 exited " + str(p.returncode))
        try:
            ws = websocket.create_connection("ws://127.0.0.1:5000/sc2api", timeout=60)
            break
        except OSError:
            time.sleep(0.2)
    if ws is None:
        raise RuntimeError("SC2 API not ready")

    def call(name, payload):
        global serial
        serial += 1
        request = sc.Request(id=serial)
        getattr(request, name).CopyFrom(payload)
        ws.send_binary(request.SerializeToString())
        response = sc.Response()
        response.ParseFromString(ws.recv())
        if response.error:
            raise RuntimeError(str(response.error))
        answer = getattr(response, name)
        if hasattr(answer, "error") and answer.HasField("error"):
            raise RuntimeError(str(answer))
        return answer

    version = call("ping", sc.RequestPing())
    if (
        version.game_version != "4.10.0.75689"
        or version.data_version != "B89B5D6FA7CBF6452E721311BFBC6CB2"
    ):
        raise ValueError("Unexpected StarCraft II engine or data version")
    print("VERSION", version, flush=True)
    call(
        "create_game",
        sc.RequestCreateGame(
            local_map=sc.LocalMap(map_path="/assets/Maps/mini_games/MoveToBeacon.SC2Map"),
            player_setup=[sc.PlayerSetup(type=sc.Participant)],
            random_seed=int(os.environ.get("SEED", "71")),
            realtime=False,
        ),
    )
    options = sc.InterfaceOptions(
        raw=False,
        score=True,
        feature_layer=sc.SpatialCameraSetup(
            width=24,
            resolution=common.Size2DI(x=64, y=64),
            minimap_resolution=common.Size2DI(x=128, y=128),
        ),
        render=sc.SpatialCameraSetup(
            resolution=common.Size2DI(x=640, y=480), minimap_resolution=common.Size2DI(x=128, y=128)
        ),
    )
    print(
        "JOIN",
        call(
            "join_game",
            sc.RequestJoinGame(race=common.Terran, options=options, player_name="GGBench"),
        ),
        flush=True,
    )
    actions = json.loads(os.environ.get("ACTIONS", "[]"))
    x, y = 64, 64
    for step in range(len(actions) + 1):
        obs = call("observation", sc.RequestObservation())
        camera = obs.observation.render_data.map
        print(
            "FRAME",
            step,
            camera.size.x,
            camera.size.y,
            camera.bits_per_pixel,
            len(camera.data),
            obs.observation.score.score,
            flush=True,
        )
        im = Image.new("RGB", (768, 480))
        im.paste(Image.frombytes("RGB", (camera.size.x, camera.size.y), camera.data), (0, 0))
        mini = obs.observation.render_data.minimap
        im.paste(Image.frombytes("RGB", (mini.size.x, mini.size.y), mini.data), (640, 0))
        im.save(out / f"sc2-{tag}-{step}.png")
        records.append(
            {
                "score": obs.observation.score.score,
                "loop": obs.observation.game_loop,
                "hash": hashlib.sha256(im.tobytes()).hexdigest(),
            }
        )
        if step == len(actions) or obs.observation.score.score > 0:
            break
        time.sleep(float(os.environ.get("DELAY", "0")))
        act = actions[step]
        if act == 1:
            y = max(0, y - 8)
        if act == 2:
            x = min(127, x + 8)
        if act == 3:
            y = min(127, y + 8)
        if act == 4:
            x = max(0, x - 8)
        if act == 7:
            y = max(0, y - 2)
        if act == 8:
            x = min(127, x + 2)
        if act == 9:
            y = min(127, y + 2)
        if act == 10:
            x = max(0, x - 2)
        if act in (5, 6):
            action = sc.Action()
            point = common.PointI(x=x, y=y)
            if act == 5:
                action.action_ui.select_army.selection_add = False
            else:
                action.action_feature_layer.unit_command.ability_id = 1
                action.action_feature_layer.unit_command.target_minimap_coord.CopyFrom(point)
            print("ACTION", call("action", sc.RequestAction(actions=[action])), flush=True)
        call("step", sc.RequestStep(count=8))
finally:
    if ws:
        ws.close()
    p.terminate()
    try:
        p.wait(3)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
    (out / f"sc2-{tag}.json").write_text(json.dumps(records, indent=2))
