#!/usr/bin/env python3
"""Check that the source-controlled architecture diagram is present and referenced."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
diagram = ROOT / "research/architecture.mmd"
readme = ROOT / "README.md"
source = diagram.read_text(encoding="utf-8") if diagram.is_file() else ""
if not source.lstrip().startswith(("flowchart", "graph")):
    raise SystemExit("research/architecture.mmd must begin with a Mermaid flowchart or graph")
if "research/architecture.mmd" not in readme.read_text(encoding="utf-8"):
    raise SystemExit("README.md must link to research/architecture.mmd")
print("Architecture diagram source and README link are present.")
