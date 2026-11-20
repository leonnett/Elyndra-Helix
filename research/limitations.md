# Known limitations

- RTL compilation, Cocotb simulation, lint, and synthesis have not run in this local-only preparation. Their first evidence must come from GitHub Actions.
- The core supports the RV32I unprivileged integer instruction set but not the privileged architecture, Zicsr, Zifencei, M, C, A, F, D, interrupts, debug, or atomics.
- `ECALL`, `EBREAK`, illegal instructions, misalignment, and bus errors are recorded and halt the core. There is no trap handler, CSR state, or return path.
- The memory protocol is a small project-local valid/ready interface, not AXI, TileLink, or Wishbone. The environment supplies read data and access-fault indications.
- There is no pipeline overlap, cache, MMU, multi-hart behavior, coherence, speculative execution, or out-of-order scheduling.
- Configuration C adds a one-entry prepared-instruction buffer but does not overlap work or promise better frequency or throughput.
- Generic Yosys cell counts do not establish physical area, timing, power, energy, process portability, or fabrication readiness.
- The test program and model are project-authored. They do not replace an official RISC-V architectural certification suite or independent third-party review.
- The repository has not been published, and no public URL or hosted CI result exists yet.
