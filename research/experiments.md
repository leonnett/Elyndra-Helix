# Experiment register

## ELY-H1-EXP-001 — HAEF generic structure comparison

**Status:** executed; functional and structural acceptance passed in GitHub Actions for code commit `a353276`.

### Question

How does generic Yosys cell structure change between a conventional add/subtract ALU (A), shared arithmetic (B), and shared arithmetic with a dedicated one-entry prepared-instruction buffer (C), when all variants use the same RV32I core source and top-level interface?

### Frozen comparison conditions

- Use the exact A/B/C top modules in `rtl/helix_core_variants.sv`.
- Use the same ordered SystemVerilog source set and Yosys version for all three variants.
- Record the SHA-256 of the source set before synthesizing each variant; the comparator refuses mismatched hashes.
- Run `synth -top <variant> -flatten`, followed by `check`, and retain Yosys logs and JSON netlists.
- Record generic total, sequential, and combinational cell counts plus all cell types and warnings.

### Acceptance

The experiment is structurally comparable only if all three lint and synthesis runs pass and report identical RTL source hashes. Results are generic-cell counts, not physical area, timing, power, energy, or application performance. A lower count is not by itself evidence of a better processor.

The passing cloud runs produced the raw logs, JUnit results, netlists, and JSON/Markdown reports as GitHub Actions artifacts. The simulation passed eight top-level suites with eleven Cocotb cases at seed `1212231729`. Verilator lint and Yosys synthesis passed for all three configurations with a common RTL source hash. Artifact IDs, digests, run links, and retention dates are recorded in `research/evidence-status.json`. These results support a generic structural comparison only; they do not establish physical performance or full RISC-V compliance.

`experiments/ELY-H1-EXP-001/protocol.json` is the frozen pre-run configuration. Its `DEFINED_PENDING_CLOUD_CI` field records the protocol's state when frozen; the live execution outcome is recorded in `research/evidence-status.json` so the experimental configuration hash remains unchanged.
