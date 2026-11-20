# Experiment register

## ELY-H1-EXP-001 — HAEF generic structure comparison

**Status:** defined; execution pending cloud CI.

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

No result is stored in this repository until the workflow actually runs. CI artifacts are the raw evidence; the Markdown and JSON reports summarize those artifacts without inventing missing values.
