"""Reference visual policies. No game imports, privileged state, or reward access."""

import base64
import io
import json
import random
import sys

import numpy as np
from PIL import Image


class PixelPolicy:
    def __init__(self, name: str):
        self.name, self.rng, self.tick = name, random.Random(1729), 0

    def act(self, obs: dict) -> int:
        self.tick += 1
        actions = obs["actions"]
        if self.name == "idle":
            return 0
        if self.name == "random":
            return self.rng.randrange(len(actions))
        im = np.asarray(Image.open(io.BytesIO(base64.b64decode(obs["image_png"]))))
        if actions == ["wait", "left", "right", "up", "down"] and im.shape[:2] == (160, 160):
            cyan = (im[:, :, 1] > 190) & (im[:, :, 2] > 190) & (im[:, :, 0] < 100)
            ys, xs = np.where(cyan)
            if not len(xs):
                return 0
            px, py = int(xs.mean() // 16), int(ys.mean() // 16)
            yellow = (im[:, :, 0] > 220) & (im[:, :, 1] > 170) & (im[:, :, 2] < 100)
            ys, xs = np.where(yellow)
            if len(xs):
                tx, ty = int(xs.mean() // 16), int(ys.mean() // 16)
                dx, dy = tx - px, ty - py
                if self.name == "tracker" and abs(dy) > abs(dx):
                    return 4 if dy > 0 else 3
                return (2 if dx > 0 else 1) if dx else (4 if dy > 0 else 3) if dy else 0
            red = (im[:, :, 0] > 220) & (im[:, :, 1] < 120)
            # React sees only the next collision row; Tracker looks farther ahead.
            start = 4 if self.name == "tracker" else 7
            risk = [
                sum(red[y * 16 + 8, x * 16 + 8] * (y + 1) for y in range(start, 8))
                for x in range(10)
            ]
            candidates = [
                (risk[x], abs(x - px), a)
                for a, x in [(0, px), (1, px - 1), (2, px + 1)]
                if 0 <= x < 10
            ]
            return min(candidates)[2]
        # A deliberately simple Doom visual baseline; not a trained FPS agent.
        if "attack" in actions:
            if self.name == "tracker" and self.tick % 4 == 0:
                movement = "turn_right" if "turn_right" in actions else "move_right"
                if movement in actions:
                    return actions.index(movement)
            return actions.index("attack")
        moves = [
            i for i, a in enumerate(actions) if a in ("move_forward", "move_left", "move_right")
        ]
        return self.rng.choice(moves) if moves else 0


def main():
    policy = PixelPolicy(sys.argv[1] if len(sys.argv) > 1 else "react")
    Image.init()  # Warm image codecs before announcing readiness, not on a scored frame.
    print(json.dumps({"ready": True}), flush=True)
    for line in sys.stdin:
        obs = json.loads(line)
        print(json.dumps({"nonce": obs["nonce"], "action": policy.act(obs)}), flush=True)


if __name__ == "__main__":
    main()
