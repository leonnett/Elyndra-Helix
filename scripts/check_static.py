#!/usr/bin/env python3
"""Static-only repository checks; this script never invokes an HDL tool."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_RTL = {
    "helix_alu.sv": "module helix_alu",
    "helix_branch.sv": "module helix_branch",
    "helix_control.sv": "module helix_control",
    "helix_core.sv": "module helix_core",
    "helix_core_variants.sv": "module helix_core_a",
    "helix_decoder.sv": "module helix_decoder",
    "helix_execution_fabric.sv": "module helix_execution_fabric",
    "helix_immediate.sv": "module helix_immediate",
    "helix_memory_interface.sv": "module helix_memory_interface",
    "helix_register_file.sv": "module helix_register_file",
}


def main() -> int:
    problems: list[str] = []
    for filename, marker in REQUIRED_RTL.items():
        path = ROOT / "rtl" / filename
        if not path.is_file() or path.stat().st_size == 0:
            problems.append(f"missing or empty RTL module: rtl/{filename}")
            continue
        if marker not in path.read_text(encoding="utf-8"):
            problems.append(f"module declaration not found in rtl/{filename}")

    module_names: list[str] = []
    for path in sorted((ROOT / "rtl").glob("*.sv")):
        module_names.extend(re.findall(r"\bmodule\s+([A-Za-z_][A-Za-z_0-9]*)", path.read_text(encoding="utf-8")))
    if len(module_names) != len(set(module_names)):
        problems.append("duplicate SystemVerilog module declaration found")
    if not {"helix_core_a", "helix_core_b", "helix_core_c"}.issubset(module_names):
        problems.append("one or more synthesizable core variants are missing")

    for path in sorted((ROOT / "tests").glob("*.py")) + sorted((ROOT / "scripts").glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            problems.append(f"Python syntax error in {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}")

    lock_path = ROOT / "toolchain.lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        if lock.get("project") != "Elyndra Helix H1":
            problems.append("toolchain.lock.json project identity is incorrect")
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"invalid toolchain.lock.json: {exc}")

    required_paths = [
        ROOT / "README.md",
        ROOT / "LICENSE",
        ROOT / ".github/workflows/simulation.yml",
        ROOT / ".github/workflows/synthesis.yml",
        ROOT / "research/architecture.mmd",
        ROOT / "tests/reference_model.py",
        ROOT / "tests/test_core.py",
    ]
    for path in required_paths:
        if not path.is_file() or path.stat().st_size == 0:
            problems.append(f"missing or empty required file: {path.relative_to(ROOT)}")

    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1
    print(f"Static checks passed for {len(REQUIRED_RTL)} RTL files, {len(module_names)} modules, and Python sources.")
    print("No compilation or simulation was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
