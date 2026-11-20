# Research methodology

## Evidence stages

1. **Source inspection:** static repository checks confirm expected module declarations, unique module names, Python syntax trees, configuration JSON, workflow presence, and diagram source. These checks do not establish RTL syntax or function.
2. **RTL lint:** Verilator checks each configuration top and retains warnings.
3. **Functional verification:** Cocotb drives directed and deterministic randomized unit cases plus processor programs. An independent Python architectural interpreter predicts retirement effects. JUnit XML, logs, seeds, input instructions, expected values, actual values, and source hashes are retained.
4. **Generic synthesis:** Yosys synthesizes each top and runs structural checks. JSON netlists and logs are retained.
5. **Comparison:** generic cell counts are compared only when source hashes and tool versions are consistent.

## Reproducibility

The tool versions and source tag are in `toolchain.lock.json`; workflow action revisions are pinned in `.github/workflows/`. The simulation default seed is `1212231729`. All source hashing is deterministic over sorted RTL paths with path separators and NUL delimiters included. The report records actual tool versions and run status.

The processor-level smoke program is encoded from `tests/programs.py`. Its input instruction sequence, committed PC, destination register, and value are checked against `tests/reference_model.py`. The model is an architectural interpreter and does not share the RTL ALU implementation.

## Interpretation limits

Verilator pass/fail applies only to modeled inputs and tested instructions. Yosys generic cells are not a technology-mapped design. Without an identified standard-cell library, constraints, physical flow, and calibrated activity, no silicon area, timing, power, energy, or real workload performance conclusion is valid. No compliance claim is made until an official compliance suite passes.
