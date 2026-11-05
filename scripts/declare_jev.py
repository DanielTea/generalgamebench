"""Freeze a native-image Jev campaign before any scored model call."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from run_campaign import WARMUP_PROFILE

from generalgamebench import __version__
from generalgamebench.jev import ACTION_SCHEMA, IMAGE_PREPROCESSING, TRANSPORT
from generalgamebench.latency import policy
from generalgamebench.model_prompt import PROMPT_VERSION

ROOT = Path(__file__).resolve().parents[1]


def declare(report, preflight):
    if (report / "campaign.json").exists():
        raise FileExistsError("Preserve the existing campaign declaration")
    snapshot_path = ROOT / "site/dist/data.json"
    snapshot = json.loads(snapshot_path.read_text())
    base = json.loads((ROOT / snapshot["current_campaign"]).read_text())
    resolved = json.loads(preflight.read_text())
    audit = report / "engine-rebuilds.json"
    if not audit.is_file() or len(json.loads(audit.read_text())["games"]) != 9:
        raise ValueError("Audit all nine rebuilt engine scenarios before declaring the run")
    model = resolved["resolved_model"]
    suite_path = ROOT / "benchmarks" / ("mac-" + report.name + ".json")
    if suite_path.exists():
        raise FileExistsError("Preserve the existing suite file")
    suite = {
        "schema_version": "generalgamebench-suite/1",
        "id": "mac-" + report.name,
        "evaluator_version": __version__,
        "games": base["games"],
        "seed_ids": base["seeds"],
        "max_steps": base["max_steps"],
        "mode": base["mode"],
        "trust": "local-unattested",
        "description": f"{model} uses native PNG input on all 43 scenarios, seed 3000 and eight decisions per game.",
    }
    suite_path.write_text(json.dumps(suite, indent=2) + "\n")
    campaign = {
        "schema_version": "generalgamebench-campaign/1",
        "id": report.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "implementation_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "model": model,
        "requested_alias": resolved["requested_alias"],
        "games": base["games"],
        "seeds": base["seeds"],
        "max_steps": base["max_steps"],
        "mode": base["mode"],
        "timeout_s": base["timeout_s"],
        "workers": 1,
        "prompt_version": PROMPT_VERSION,
        "action_schema": ACTION_SCHEMA,
        "image_preprocessing": IMAGE_PREPROCESSING,
        "transport": TRANSPORT,
        "warmup": WARMUP_PROFILE,
        "latency_policy": policy(),
        "run_root": f"runs/{report.name}/episodes",
        "suite_file": str(suite_path.relative_to(ROOT)),
        "base_campaign": snapshot["current_campaign"],
        "base_snapshot_sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
        "engine_rebuild_audit": str(audit.relative_to(ROOT)),
        "engine_rebuild_sha256": hashlib.sha256(audit.read_bytes()).hexdigest(),
        "scope": "One seed and eight decisions per scenario check integration. These short runs cannot establish model skill.",
        "hardware_details": "Apple M3 Max; 48 GiB RAM; 16 CPU cores; macOS arm64. One model and one game run at a time. Jev uses a persistent direct HTTPS connection and native multipart PNG input. Frames with either dimension below 280 pixels use integer nearest-neighbor upscaling; the full frame and aspect ratio are preserved. Image preparation remains in the timer. Three uniform gray startup calls occur before scoring. The original frozen prompt supplies the rules and controls; a native Choice schema supplies the same integer action options. There is no OCR, text description of the frame, tool use, retry, or fallback action. The nine container engines were rebuilt from their pinned sources. Their new image IDs and fixed-trace replay checks are in the campaign report. Provider hardware is not known. Normal desktop tasks can use the same Mac.",
        "timing_note": "The clock includes frame capture, PNG encoding, multipart encoding, network transfer, provider inference, parsing and action validation. Game advancement is outside the clock. Use all recorded times, including failures, for suite p95 below 200 ms. Exactly 200 ms fails. The simulation waits for each action.",
        "failure_note": "Keep every scored error and aborted episode. Aborted episodes score zero. Do not replace failures. Publish an aggregate only after all 43 episodes pass native replay.",
        "publication_note": "Keep all previous model rows unchanged. Append one complete local-unattested Jev image suite to the model exhibition. Keep the official ranking separate.",
        "comparison_note": "Models use the same task definitions, scenarios, seed and decision horizon. Jev uses native Choice output, integer nearest-neighbor upscaling for frames below the API minimum, and a persistent image API; earlier hosted models use a fresh CLI process per frame. Jev's nine container engines have new image IDs from pinned source rebuilds. One fixed previous camera and score trace per rebuilt scenario passed exact replay. This does not establish equivalence for every possible trajectory. Each row retains its actual engine IDs and transport. Timings measure the full response path, not model-only inference.",
    }
    source_paths = set(base["source_hashes"]) | {
        "src/generalgamebench/jev.py",
        "scripts/run_jev.py",
        "scripts/preflight_jev.py",
        "scripts/export_jev.py",
        "scripts/declare_jev.py",
        "scripts/verify_rebuilt_engines.py",
        str(suite_path.relative_to(ROOT)),
    }
    campaign["source_hashes"] = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in sorted(source_paths)
    }
    report.mkdir(parents=True, exist_ok=True)
    (report / "model-preflight.json").write_text(json.dumps(resolved, indent=2) + "\n")
    (report / "campaign.json").write_text(json.dumps(campaign, indent=2) + "\n")
    print(json.dumps({"campaign": report.name, "model": model, "scenarios": len(base["games"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    args = parser.parse_args()
    declare(args.report.resolve(), args.preflight.resolve())
