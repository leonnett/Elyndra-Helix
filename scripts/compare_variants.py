#!/usr/bin/env python3
"""Compare only measured generic Yosys structure across HAEF configurations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/synthesis/synthesis-report.json"
OUT = ROOT / "results/comparison"


def main() -> int:
    if not SOURCE.is_file():
        raise SystemExit("missing results/synthesis/synthesis-report.json; run make synthesis in cloud CI first")
    synthesis = json.loads(SOURCE.read_text(encoding="utf-8"))
    variants = synthesis.get("configurations", {})
    if synthesis.get("status") != "passed" or set(variants) != {"A", "B", "C"}:
        raise SystemExit("all three synthesis configurations must pass before comparison")
    hashes = {item.get("source_sha256") for item in variants.values()}
    if len(hashes) != 1:
        raise SystemExit("variant source hashes differ; refusing an incomparable comparison")

    comparisons = []
    for left, right, description in [
        ("A", "B", "shared arithmetic versus conventional datapath"),
        ("B", "C", "one-entry prepared-instruction buffer versus shared baseline"),
        ("A", "C", "combined shared arithmetic and prepared-instruction buffer versus conventional datapath"),
    ]:
        a = variants[left]
        b = variants[right]
        comparisons.append(
            {
                "left": left,
                "right": right,
                "description": description,
                "generic_cell_delta": b["generic_cell_count"] - a["generic_cell_count"],
                "sequential_cell_delta": b["sequential_cell_count"] - a["sequential_cell_count"],
                "combinational_cell_delta": b["combinational_cell_count"] - a["combinational_cell_count"],
            }
        )
    report = {
        "schema_version": 1,
        "experiment_id": "ELY-H1-EXP-001",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "rtl_source_sha256": next(iter(hashes)),
        "measurement": "generic Yosys cell structure; not physical area, timing, power, or workload performance",
        "variants": variants,
        "comparisons": comparisons,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "variant-comparison.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# HAEF configuration comparison",
        "",
        f"- Experiment: `{report['experiment_id']}`",
        f"- Status: **{report['status'].upper()}**",
        f"- RTL SHA-256: `{report['rtl_source_sha256']}`",
        "- Metric: generic Yosys cell structure only",
        "",
        "| Comparison | Cell delta | Sequential delta | Combinational delta |",
        "|---|---:|---:|---:|",
    ]
    for item in comparisons:
        lines.append(
            f"| {item['left']} → {item['right']} ({item['description']}) | {item['generic_cell_delta']:+d} | "
            f"{item['sequential_cell_delta']:+d} | {item['combinational_cell_delta']:+d} |"
        )
    lines.extend(
        [
            "",
            "These deltas are structural counts from the captured generic netlists. No technology library, timing constraints, switching activity, physical area, power, or performance workload is modeled.",
            "",
        ]
    )
    (OUT / "variant-comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote generic structural comparison for configurations A, B, and C.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
