# Helix Core H1 architecture

## Scope

Helix Core H1 is a 32-bit, single-hart, in-order processor for the RV32I base integer ISA. The RTL is designed to be synthesizable by Verilator and Yosys, but its syntax and behavior remain unverified until cloud CI completes. No RISC-V compliance suite has run.

## Execution model

The core uses a finite-state controller with fetch, decode, optional preparation, execute, memory, writeback, and halted states. Configuration A and B move from decode to execute. Configuration C stores one decoded instruction and its operands in a dedicated preparation buffer, then transfers that entry into the execution registers. Only one instruction is active, and only one memory request can be outstanding. There is no pipeline overlap, forwarding, speculation, out-of-order issue, or cache coherence.

The common memory bus carries instruction requests and data requests. `mem_valid && mem_ready` completes a request. `mem_error` is sampled with that handshake. Fetch uses byte address `pc`; data accesses align the bus address down to four bytes and use little-endian byte strobes. Byte, halfword, and word accesses are supported. Naturally misaligned halfword and word accesses trap before a bus request.

## Instruction and trap behavior

The supported instruction encodings are the base RV32I integer arithmetic/logical operations, immediate operations, branches, jumps, loads, stores, `LUI`, `AUIPC`, `FENCE`, `ECALL`, and `EBREAK`. `FENCE` has no extra datapath action because every request completes before the next instruction starts. Reserved encodings, `FENCE.I`, and unsupported extensions are illegal.

The core exposes cause, PC, and trap value and enters a permanent halted state. Implemented causes are instruction-address-misaligned (0), instruction access fault (1), illegal instruction (2), breakpoint (3), load-address-misaligned (4), load access fault (5), store-address-misaligned (6), store access fault (7), and environment call (11). Cause 11 is the machine-mode ECALL encoding; Helix has no privilege-mode state, so this is an explicit core contract rather than a privilege implementation. Trap values follow the faulting address for address-related traps and the instruction word for illegal instructions.

The core has no privileged CSR file, trap vector, interrupt inputs, software exception return, or debug module. This is an execution research core, not a complete privileged RISC-V system.

## Helix Adaptive Execution Fabric

HAEF varies two bounded design choices: the adder arrangement and whether a dedicated one-entry prepared-instruction buffer is present. The configurations preserve the same ISA, memory ordering, and retirement contract. Their meaningful initial comparison is generic netlist structure after synthesis; no throughput advantage is implied.
