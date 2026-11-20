#!/usr/bin/env python3
"""Run Verilator lint and generic Yosys synthesis for HAEF configurations."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RTL_SOURCES = sorted((ROOT / "rtl").glob("*.sv"))
VARIANTS = {"A": "helix_core_a", "B": "helix_core_b", "C": "helix_core_c"}
YOSYS_COMMAND = "yowasp-yosys"


def sha256_sources(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def first_line(command: list[str]) -> str:
    try:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        lines = (completed.stdout or completed.stderr).strip().splitlines()
        return lines[0] if lines else "unavailable"
    except OSError:
        return "unavailable"


def run(command: list[str], log_path: Path) -> tuple[int, str]:
    try:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        return_code = completed.returncode
        output = completed.stdout + completed.stderr
    except OSError as exc:
        return_code = 127
        output = f"Unable to start {command[0]}: {exc}\n"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output, encoding="utf-8")
    return return_code, output


def flip_flop_cell(cell_type: str) -> bool:
    upper = cell_type.upper()
    return "DFF" in upper or "DLATCH" in upper or upper.startswith("$MEM")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lint-only", action="store_true")
    args = parser.parse_args()
    result_dir = ROOT / "results/synthesis"
    netlist_dir = ROOT / "build/synthesis"
    result_dir.mkdir(parents=True, exist_ok=True)
    netlist_dir.mkdir(parents=True, exist_ok=True)
    source_hash = sha256_sources(RTL_SOURCES)
    report: dict[str, object] = {
        "schema_version": 1,
        "experiment_id": "ELY-H1-EXP-001",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "mode": "lint-only" if args.lint_only else "generic-synthesis",
        "rtl_source_sha256": source_hash,
        "tool_versions": {
            "python": sys.version.split()[0],
            "verilator": first_line(["verilator", "--version"]),
            "yosys": first_line([YOSYS_COMMAND, "-V"]) if not args.lint_only else "not run",
        },
        "configurations": {},
    }
    source_list = [path.relative_to(ROOT).as_posix() for path in RTL_SOURCES]
    failed = False

    for name, top in VARIANTS.items():
        lint_log = result_dir / f"lint-{name}.log"
        lint_command = ["verilator", "--lint-only", "--timing", "-Wall", "-Wno-fatal", "--top-module", top, *source_list]
        lint_status, lint_output = run(lint_command, lint_log)
        lint_warnings = [line.strip() for line in lint_output.splitlines() if re.search(r"%Warning|Warning:", line)]
        item: dict[str, object] = {
            "top": top,
            "lint_status": "passed" if lint_status == 0 else "failed",
            "lint_exit_code": lint_status,
            "lint_log": lint_log.relative_to(ROOT).as_posix(),
            "lint_warning_count": len(lint_warnings),
            "lint_warnings": lint_warnings,
            "source_sha256": source_hash,
        }
        if lint_status != 0:
            failed = True

        if not args.lint_only:
            netlist = netlist_dir / f"{name.lower()}.json"
            quoted_sources = " ".join(source_list)
            yosys_script = (
                f"read_verilog -sv {quoted_sources}; "
                f"hierarchy -check -top {top}; "
                f"synth -top {top} -flatten; "
                f"check; "
                f"write_json {netlist.relative_to(ROOT).as_posix()}"
            )
            synth_log = result_dir / f"synthesis-{name}.log"
            synthesis_status, synthesis_output = run([YOSYS_COMMAND, "-p", yosys_script], synth_log)
            warnings = [line.strip() for line in synthesis_output.splitlines() if "Warning:" in line]
            if synthesis_status == 0 and netlist.is_file():
                design = json.loads(netlist.read_text(encoding="utf-8"))
                cells = design.get("modules", {}).get(top, {}).get("cells", {})
                cell_counts = Counter(cell.get("type", "unknown") for cell in cells.values())
                sequential = sum(count for kind, count in cell_counts.items() if flip_flop_cell(kind))
                total = sum(cell_counts.values())
                item.update(
                    {
                        "synthesis_status": "passed",
                        "synthesis_exit_code": synthesis_status,
                        "synthesis_log": synth_log.relative_to(ROOT).as_posix(),
                        "synthesis_warning_count": len(warnings),
                        "synthesis_warnings": warnings,
                        "generic_cell_count": total,
                        "sequential_cell_count": sequential,
                        "combinational_cell_count": total - sequential,
                        "generic_cell_types": dict(sorted(cell_counts.items())),
                        "netlist_json": netlist.relative_to(ROOT).as_posix(),
                    }
                )
            else:
                failed = True
                item.update(
                    {
                        "synthesis_status": "failed",
                        "synthesis_exit_code": synthesis_status,
                        "synthesis_log": synth_log.relative_to(ROOT).as_posix(),
                        "synthesis_warning_count": len(warnings),
                        "synthesis_warnings": warnings,
                    }
                )
        report["configurations"][name] = item

    if failed:
        report["status"] = "failed"
    suffix = "lint-report" if args.lint_only else "synthesis-report"
    (result_dir / f"{suffix}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# " + ("RTL lint evidence" if args.lint_only else "Generic synthesis evidence"),
        "",
        f"- Experiment: `{report['experiment_id']}`",
        f"- Status: **{report['status'].upper()}**",
        f"- RTL SHA-256: `{source_hash}`",
        f"- Verilator: `{report['tool_versions']['verilator']}`",
    ]
    if not args.lint_only:
        lines.append(f"- Yosys: `{report['tool_versions']['yosys']}`")
        lines.extend(["", "| Configuration | Lint | Yosys | Generic cells | Sequential cells | Combinational cells | Warnings |", "|---|---:|---:|---:|---:|---:|---:|"])
        for name, item in report["configurations"].items():
            lines.append(
                f"| {name} | {item['lint_status']} | {item['synthesis_status']} | {item.get('generic_cell_count', 'n/a')} | "
                f"{item.get('sequential_cell_count', 'n/a')} | {item.get('combinational_cell_count', 'n/a')} | "
                f"{item['lint_warning_count'] + item.get('synthesis_warning_count', 0)} |"
            )
    else:
        lines.extend(["", "| Configuration | Lint | Warnings |", "|---|---:|---:|"])
        for name, item in report["configurations"].items():
            lines.append(f"| {name} | {item['lint_status']} | {item['lint_warning_count']} |")
    lines.extend(["", "Generic cell counts describe this Yosys netlist only. They are not silicon area, timing, power, or performance measurements.", ""])
    (result_dir / f"{suffix}.md").write_text("\n".join(lines), encoding="utf-8")
    for name, item in report["configurations"].items():
        print(f"Configuration {name}: lint={item['lint_status']} synthesis={item.get('synthesis_status', 'not run')}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
