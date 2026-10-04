"""Build the public snapshot only from replay-verified complete campaigns."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from screenquest_arena.evidence import read_ledger, verify_episode
from screenquest_arena.games import DOOM, NATIVE
from screenquest_arena.ranking import summarize

root = Path(__file__).resolve().parents[1]


def load_campaign(relative, expected_count):
    folders = sorted((root / relative).glob("*/*/events.jsonl"))
    if len(folders) != expected_count:
        raise ValueError(f"{relative}: expected {expected_count} episodes, found {len(folders)}")
    results = []
    roots = {}
    for i, path in enumerate(folders):
        verify_episode(path.parent)
        result = read_ledger(path)[-1]
        results.append(result)
        roots[str(path.relative_to(root))] = json.loads(path.read_text().splitlines()[-1])["hash"]
        if (i + 1) % 50 == 0:
            print(f"Verified {i + 1}/{len(folders)} episodes from {relative}", flush=True)
    return results, roots


local, roots1 = load_campaign("runs/baselines-final", 400)
exhibition, roots2 = load_campaign("runs/exhibition-final", 36)
local_board = summarize(local, list(NATIVE + DOOM), list(range(1000, 1010)))
model_board = summarize(exhibition, ["coin-run", "dodge-lanes", "doom-basic"], [2000, 2001])
for name, board in [("baselines", local_board), ("exhibition", model_board)]:
    (root / "results" / f"{name}.json").write_text(json.dumps({"rankings": board}, indent=2) + "\n")
public = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "season": "0.1.0",
    "local": local_board,
    "exhibition": model_board,
    "official": [],
    "catalog": json.loads((root / "docs/catalog.json").read_text()),
}
(root / "site/dist/data.json").write_text(json.dumps(public, indent=2) + "\n")
(root / "results/episodes.json").write_text(json.dumps(local + exhibition, indent=2) + "\n")
(root / "results/evidence-roots.json").write_text(json.dumps(roots1 | roots2, indent=2) + "\n")
source = {
    str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted((root / "src/screenquest_arena").glob("*.py"))
}
source["uv.lock"] = hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest()
(root / "results/source-hashes.json").write_text(json.dumps(source, indent=2) + "\n")
print(
    json.dumps(
        {
            "episodes": len(local + exhibition),
            "decisions": sum(r["steps"] for r in local + exhibition),
            "local": [(r["agent"], r["score"], r["max_ms"]) for r in local_board],
            "exhibition": [(r["agent"], r["score"], r["max_ms"]) for r in model_board],
        }
    ),
    flush=True,
)
