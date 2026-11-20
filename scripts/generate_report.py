#!/usr/bin/env python3
"""Generate a compact report from whichever cloud evidence artifacts are present."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=("all", "simulation", "synthesis"), default="all")
    args = parser.parse_args()
    simulation = read_json(ROOT / "results/simulation/simulation-report.json")
    synthesis = read_json(ROOT / "results/synthesis/synthesis-report.json")
    comparison = read_json(ROOT / "results/comparison/variant-comparison.json")
    selected = {
        "simulation": simulation if args.scope in ("all", "simulation") else None,
        "synthesis": synthesis if args.scope in ("all", "synthesis") else None,
        "comparison": comparison if args.scope in ("all", "synthesis") else None,
    }
    included = [item for item in selected.values() if item is not None]
    if not included:
        raise SystemExit("no evidence artifacts are present for the requested scope")
    hashes = {item.get("rtl_source_sha256") for item in included if item.get("rtl_source_sha256")}
    status = "passed" if all(item.get("status") == "passed" for item in included) else "failed"
    if len(hashes) > 1:
        status = "incomparable-source-hashes"
    report = {
        "schema_version": 1,
        "experiment_id": "ELY-H1-EXP-001",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": args.scope,
        "status": status,
        "rtl_source_sha256": sorted(hashes),
        "evidence": selected,
    }
    out_dir = ROOT / "results/report"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.scope}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# Elyndra Helix evidence report ({args.scope})",
        "",
        f"- Experiment: `{report['experiment_id']}`",
        f"- Status: **{status.upper()}**",
        f"- Source hash: `{', '.join(report['rtl_source_sha256']) or 'not recorded'}`",
        "",
    ]
    for label, item in selected.items():
        if item is not None:
            lines.append(f"- {label.title()} evidence: **{item.get('status', 'unknown').upper()}**")
    if not included or args.scope == "all" and (simulation is None or synthesis is None):
        lines.extend(["", "One or more evidence classes are missing. No result is inferred for a missing class."])
    lines.extend(["", "Generic synthesis counts are not physical area, power, or timing. Simulation results cover only the recorded deterministic programs and tests.", ""])
    (out_dir / f"{args.scope}.md").write_text("\n".join(lines), encoding="utf-8")
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
