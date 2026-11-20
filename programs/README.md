# Processor programs

The processor-level smoke program is built deterministically by [`tests/programs.py`](../tests/programs.py), which is also its single machine-code source of truth. It covers the RV32I base integer instruction families, signed and unsigned comparisons, each branch predicate, jumps, byte/halfword/word loads and stores, `FENCE`, and a terminating `EBREAK`.

The test emits instruction words directly with small format encoders. It does not depend on a local RISC-V assembler or an unpinned compiler. The independent Python interpreter consumes the resulting instruction stream from memory and compares every committed instruction and destination value.
