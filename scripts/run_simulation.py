#!/usr/bin/env python3
"""Run the Cocotb/Verilator suites and record reproducible test evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RTL_SOURCES = sorted((ROOT / "rtl").glob("*.sv"))
SUITES = [
    ("helix_alu", "test_alu"),
    ("helix_branch", "test_branch"),
    ("helix_decoder", "test_decoder"),
    ("helix_immediate", "test_immediate"),
    ("helix_register_file", "test_register_file"),
    ("helix_core_a", "test_core"),
    ("helix_core_b", "test_core"),
    ("helix_core_c", "test_core"),
]


def sha256_sources(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def tool_version(command: list[str]) -> str:
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        return (result.stdout or result.stderr).strip().splitlines()[0]
    except (OSError, IndexError):
        return "unavailable"


def cocotb_version() -> str:
    try:
        completed = subprocess.run(
            [sys.executable, "-c", "import cocotb; print(cocotb.__version__)"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        return completed.stdout.strip() if completed.returncode == 0 else "unavailable"
    except OSError:
        return "unavailable"


def parse_testcases(xml_path: Path) -> list[dict[str, object]]:
    if not xml_path.is_file():
        return []
    root = ET.parse(xml_path).getroot()
    tests: list[dict[str, object]] = []
    for case in root.iter("testcase"):
        failure = case.find("failure")
        error = case.find("error")
        tests.append(
            {
                "name": case.attrib.get("name", "unknown"),
                "classname": case.attrib.get("classname", ""),
                "status": "failed" if failure is not None or error is not None else "passed",
                "duration_seconds": float(case.attrib.get("time", "0")),
                "failure_location": (failure if failure is not None else error).attrib.get("message", "") if (failure is not None or error is not None) else None,
                "failure_details": ((failure if failure is not None else error).text or "") if (failure is not None or error is not None) else None,
            }
        )
    return tests


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("all", "unit", "core"), default="all")
    parser.add_argument("--seed", default=os.environ.get("HELIX_SEED", "1212231729"))
    args = parser.parse_args()
    seed = int(args.seed, 0)
    report_dir = ROOT / "results/simulation"
    build_root = ROOT / "build/simulation"
    report_dir.mkdir(parents=True, exist_ok=True)
    build_root.mkdir(parents=True, exist_ok=True)

    suites = SUITES
    if args.suite == "unit":
        suites = SUITES[:5]
    elif args.suite == "core":
        suites = SUITES[5:]

    makefiles = subprocess.run(["cocotb-config", "--makefiles"], cwd=ROOT, text=True, capture_output=True, check=False)
    if makefiles.returncode != 0:
        report = {
            "schema_version": 1,
            "experiment_id": "ELY-H1-EXP-001",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "seed": seed,
            "tool_versions": {
                "python": sys.version.split()[0],
                "cocotb": cocotb_version(),
                "verilator": tool_version(["verilator", "--version"]),
            },
            "rtl_source_sha256": sha256_sources(RTL_SOURCES),
            "suites": [],
            "setup_error": (makefiles.stdout + makefiles.stderr).strip(),
        }
        (report_dir / "simulation-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (report_dir / "simulation-report.md").write_text(
            "# Simulation evidence\n\n- Status: **FAILED BEFORE TEST DISCOVERY**\n"
            f"- Seed: `{seed}`\n- RTL SHA-256: `{report['rtl_source_sha256']}`\n\n"
            f"Setup error: `{report['setup_error']}`\n",
            encoding="utf-8",
        )
        print(report["setup_error"], file=sys.stderr)
        return 2
    makefile = Path(makefiles.stdout.strip()) / "Makefile.sim"
    all_results: list[dict[str, object]] = []
    overall_status = "passed"
    for top, module in suites:
        top_build = build_root / top
        top_build.mkdir(parents=True, exist_ok=True)
        junit = top_build / "results.xml"
        log_path = report_dir / f"{top}.log"
        relative_sources = " ".join(path.relative_to(ROOT).as_posix() for path in RTL_SOURCES)
        command = [
            "make",
            "-f",
            str(makefile),
            "SIM=verilator",
            "TOPLEVEL_LANG=verilog",
            f"COCOTB_TOPLEVEL={top}",
            f"COCOTB_TEST_MODULES={module}",
            f"VERILOG_SOURCES={relative_sources}",
            f"SIM_BUILD={top_build.relative_to(ROOT).as_posix()}",
            f"COCOTB_RESULTS_FILE={junit.relative_to(ROOT).as_posix()}",
        ]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join([str(ROOT / "tests"), environment.get("PYTHONPATH", "")]).rstrip(os.pathsep)
        environment["HELIX_SEED"] = str(seed)
        completed = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")
        testcases = parse_testcases(junit)
        status = "passed" if completed.returncode == 0 and bool(testcases) and all(item["status"] == "passed" for item in testcases) else "failed"
        if status != "passed":
            overall_status = "failed"
        all_results.append(
            {
                "top": top,
                "module": module,
                "status": status,
                "exit_code": completed.returncode,
                "seed": seed,
                "command": command,
                "log": log_path.relative_to(ROOT).as_posix(),
                "junit": junit.relative_to(ROOT).as_posix() if junit.exists() else None,
                "testcases": testcases,
            }
        )
        print(f"{top}: {status} ({len(testcases)} Cocotb test cases)")

    report = {
        "schema_version": 1,
        "experiment_id": "ELY-H1-EXP-001",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": overall_status,
        "seed": seed,
        "tool_versions": {
            "python": sys.version.split()[0],
            "cocotb": cocotb_version(),
            "verilator": tool_version(["verilator", "--version"]),
        },
        "rtl_source_sha256": sha256_sources(RTL_SOURCES),
        "suites": all_results,
    }
    json_path = report_dir / "simulation-report.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Simulation evidence",
        "",
        f"- Experiment: `{report['experiment_id']}`",
        f"- Status: **{overall_status.upper()}**",
        f"- Seed: `{seed}`",
        f"- RTL SHA-256: `{report['rtl_source_sha256']}`",
        f"- Python: `{report['tool_versions']['python']}`",
        f"- Verilator: `{report['tool_versions']['verilator']}`",
        "",
        "| Top | Test module | Status | Cases |",
        "|---|---|---:|---:|",
    ]
    lines.extend(f"| `{item['top']}` | `{item['module']}` | {item['status']} | {len(item['testcases'])} |" for item in all_results)
    lines.extend(["", "Test logs and JUnit XML contain failure locations and assertion context. No silicon, timing, or power claims are made.", ""])
    (report_dir / "simulation-report.md").write_text("\n".join(lines), encoding="utf-8")
    return 0 if overall_status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
