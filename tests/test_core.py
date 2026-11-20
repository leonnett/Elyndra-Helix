import os

import cocotb
from cocotb.triggers import Timer

from programs import build_rv32i_smoke
from reference_model import RV32IReference


MEMORY_BYTES = 4096
SEED = int(os.environ.get("HELIX_SEED", "1212231729"), 0)


def put_word(memory: bytearray, address: int, value: int) -> None:
    memory[address : address + 4] = (value & 0xFFFFFFFF).to_bytes(4, "little")


def get_word(memory: bytearray, address: int) -> int:
    return int.from_bytes(memory[address : address + 4], "little")


async def reset_core(dut, memory: bytearray) -> None:
    dut.clk.value = 0
    dut.reset_n.value = 0
    dut.mem_read_data.value = 0
    dut.mem_ready.value = 0
    dut.mem_error.value = 0
    await Timer(2, unit="ns")
    dut.clk.value = 1
    await Timer(2, unit="ns")
    dut.clk.value = 0
    dut.reset_n.value = 1
    await Timer(1, unit="ns")


async def cycle(
    dut,
    memory: bytearray,
    bus_errors: set[int] | None = None,
    ready: bool = True,
) -> dict[str, int | bool]:
    errors = bus_errors or set()
    dut.clk.value = 0
    await Timer(1, unit="ns")
    valid = bool(int(dut.mem_valid.value))
    write = bool(int(dut.mem_write.value))
    address = int(dut.mem_address.value) if valid else 0
    write_data = int(dut.mem_write_data.value) if valid else 0
    strobes = int(dut.mem_write_strobes.value) if valid else 0
    error = valid and ready and address in errors
    read_data = get_word(memory, address) if valid and not write else 0
    dut.mem_ready.value = int(ready)
    dut.mem_error.value = int(error)
    dut.mem_read_data.value = read_data
    await Timer(1, unit="ns")
    dut.clk.value = 1
    await Timer(1, unit="ns")

    if valid and ready and write and not error:
        for lane in range(4):
            if strobes & (1 << lane):
                target = address + lane
                memory[target] = (write_data >> (lane * 8)) & 0xFF

    observed: dict[str, int | bool] = {
        "request": valid,
        "request_write": write,
        "request_address": address,
        "request_data": write_data,
        "request_strobes": strobes,
        "request_ready": ready,
        "request_error": error,
        "retire": bool(int(dut.retire_valid.value)),
        "retire_pc": int(dut.retire_pc.value),
        "retire_instruction": int(dut.retire_instruction.value),
        "retire_rd_write": bool(int(dut.retire_rd_write.value)),
        "retire_rd": int(dut.retire_rd.value),
        "retire_rd_data": int(dut.retire_rd_data.value),
        "retire_mem_access": bool(int(dut.retire_mem_access.value)),
        "retire_mem_write": bool(int(dut.retire_mem_write.value)),
        "retire_mem_address": int(dut.retire_mem_address.value),
        "retire_mem_strobes": int(dut.retire_mem_strobes.value),
        "retire_mem_data": int(dut.retire_mem_data.value),
        "trap": bool(int(dut.trap_valid.value)),
        "trap_cause": int(dut.trap_cause.value),
        "trap_pc": int(dut.trap_pc.value),
        "trap_value": int(dut.trap_value.value),
        "debug_state": int(dut.debug_state.value),
    }
    return observed


async def run_program(dut, words: list[int], bus_errors: set[int] | None = None, max_cycles: int = 1200):
    memory = bytearray(MEMORY_BYTES)
    for index, word in enumerate(words):
        put_word(memory, index * 4, word)
    reference = RV32IReference(memory)
    await reset_core(dut, memory)
    commits = 0
    stalled_request: tuple[int, bool, int, int] | None = None

    for cycle_index in range(max_cycles):
        ready = cycle_index % 11 not in (3, 4)
        observed = await cycle(dut, memory, bus_errors, ready=ready)
        if observed["request"]:
            request_signature = (
                int(observed["request_address"]),
                bool(observed["request_write"]),
                int(observed["request_data"]),
                int(observed["request_strobes"]),
            )
            if stalled_request is not None:
                assert request_signature == stalled_request, (
                    f"test_core_program_execution seed={SEED} cycle={cycle_index} "
                    f"expected_stable_request={stalled_request} actual_request={request_signature}"
                )
            stalled_request = request_signature if not ready else None
        else:
            stalled_request = None
        if observed["retire"]:
            expected_pc = reference.pc
            expected_instruction = get_word(reference.memory, expected_pc)
            instruction = int(observed["retire_instruction"])
            assert int(observed["retire_pc"]) == expected_pc, (
                f"test_core_program_execution seed={SEED} cycle={cycle_index} instruction=0x{instruction:08x} "
                f"expected_pc=0x{expected_pc:08x} actual_pc=0x{int(observed['retire_pc']):08x} state={observed['debug_state']}"
            )
            assert instruction == expected_instruction, (
                f"test_core_program_execution seed={SEED} cycle={cycle_index} pc=0x{expected_pc:08x} "
                f"expected_instruction=0x{expected_instruction:08x} actual_instruction=0x{instruction:08x}"
            )
            expected = reference.step(expected_instruction)
            assert bool(observed["retire_rd_write"]) == expected.rd_write, (
                f"test_core_program_execution seed={SEED} pc=0x{expected_pc:08x} instruction=0x{instruction:08x} "
                f"expected_rd_write={expected.rd_write} actual_rd_write={observed['retire_rd_write']}"
            )
            if expected.rd_write:
                assert int(observed["retire_rd"]) == expected.rd, (
                    f"test_core_program_execution seed={SEED} pc=0x{expected_pc:08x} instruction=0x{instruction:08x} "
                    f"expected_rd=x{expected.rd} actual_rd=x{int(observed['retire_rd'])}"
                )
                assert int(observed["retire_rd_data"]) == expected.rd_data, (
                    f"test_core_program_execution seed={SEED} pc=0x{expected_pc:08x} instruction=0x{instruction:08x} "
                    f"expected_result=0x{expected.rd_data:08x} actual_result=0x{int(observed['retire_rd_data']):08x}"
                )
            assert bool(observed["retire_mem_access"]) == expected.mem_access, (
                f"test_core_program_execution seed={SEED} pc=0x{expected_pc:08x} instruction=0x{instruction:08x} "
                f"expected_mem_access={expected.mem_access} actual_mem_access={observed['retire_mem_access']}"
            )
            if expected.mem_access:
                assert bool(observed["retire_mem_write"]) == expected.mem_write, (
                    f"test_core_program_execution seed={SEED} pc=0x{expected_pc:08x} instruction=0x{instruction:08x} "
                    f"expected_mem_write={expected.mem_write} actual_mem_write={observed['retire_mem_write']}"
                )
                assert int(observed["retire_mem_address"]) == expected.mem_address, (
                    f"test_core_program_execution seed={SEED} pc=0x{expected_pc:08x} instruction=0x{instruction:08x} "
                    f"expected_address=0x{expected.mem_address:08x} actual_address=0x{int(observed['retire_mem_address']):08x}"
                )
                if expected.mem_write:
                    assert int(observed["retire_mem_strobes"]) == expected.mem_strobes, (
                        f"test_core_program_execution seed={SEED} pc=0x{expected_pc:08x} instruction=0x{instruction:08x} "
                        f"expected_strobes=0x{expected.mem_strobes:x} actual_strobes=0x{int(observed['retire_mem_strobes']):x}"
                    )
                    assert int(observed["retire_mem_data"]) == expected.mem_data, (
                        f"test_core_program_execution seed={SEED} pc=0x{expected_pc:08x} instruction=0x{instruction:08x} "
                        f"expected_data=0x{expected.mem_data:08x} actual_data=0x{int(observed['retire_mem_data']):08x}"
                    )
            commits += 1
        if observed["trap"]:
            return memory, reference, commits, observed

    raise AssertionError(f"test_core_program_execution seed={SEED} exceeded {max_cycles} cycles; no trap observed")


@cocotb.test()
async def test_core_program_execution(dut):
    words = build_rv32i_smoke()
    memory, reference, commits, trap = await run_program(dut, words)
    assert int(trap["trap_cause"]) == 3, (
        f"test_core_program_execution seed={SEED} instruction=EBREAK expected_cause=3 actual={trap['trap_cause']} "
        f"pc=0x{int(trap['trap_pc']):08x} value=0x{int(trap['trap_value']):08x}"
    )
    assert int(trap["trap_pc"]) == reference.pc, (
        f"test_core_program_execution seed={SEED} expected_ebreak_pc=0x{reference.pc:08x} "
        f"actual=0x{int(trap['trap_pc']):08x}"
    )
    assert commits > 40, f"test_core_program_execution seed={SEED} expected broad ISA coverage; commits={commits}"
    for address in range(0x300, 0x30A):
        assert memory[address] == reference.memory[address], (
            f"test_core_program_execution seed={SEED} address=0x{address:08x} "
            f"expected_memory=0x{reference.memory[address]:02x} actual_memory=0x{memory[address]:02x}"
        )


async def expect_trap(dut, words: list[int], cause: int, pc: int, value: int = 0, bus_errors: set[int] | None = None):
    _, _, _, trap = await run_program(dut, words, bus_errors=bus_errors)
    actual = (int(trap["trap_cause"]), int(trap["trap_pc"]), int(trap["trap_value"]))
    wanted = (cause, pc, value & 0xFFFFFFFF)
    assert actual == wanted, (
        f"test_core_precise_exceptions seed={SEED} instruction=0x{words[min(pc // 4, len(words) - 1)]:08x} "
        f"input_state={{pc:0x{pc:08x},program:{[f'0x{word:08x}' for word in words]}}} "
        f"expected_trap={wanted} actual_trap={actual} state={trap['debug_state']}"
    )
    assert int(trap["debug_state"]) == 6, f"test_core_precise_exceptions seed={SEED} core must halt on trap"


@cocotb.test()
async def test_core_precise_exceptions(dut):
    from encoders import encode_i, encode_s

    await expect_trap(dut, [0xFFFFFFFF], cause=2, pc=0, value=0xFFFFFFFF)
    await expect_trap(dut, [0x0000100F], cause=2, pc=0, value=0x0000100F)
    await expect_trap(dut, [0x00000073], cause=11, pc=0)
    await expect_trap(dut, [0x00100073], cause=3, pc=0)
    await expect_trap(dut, [encode_i(1, 0, 1), encode_i(2, 1, 0, 2, 0x03)], cause=4, pc=4, value=1)
    await expect_trap(dut, [encode_i(1, 0, 1), encode_s(1, 2, 0, 2)], cause=6, pc=4, value=1)
    await expect_trap(dut, [encode_i(1, 0, 2, 0, 0x67)], cause=0, pc=0, value=2)
    await expect_trap(dut, [0x00000013], cause=1, pc=0, value=0, bus_errors={0})
    await expect_trap(
        dut,
        [encode_i(1, 0, 0x300), encode_i(2, 1, 0, 2, 0x03)],
        cause=5,
        pc=4,
        value=0x300,
        bus_errors={0x300},
    )
    await expect_trap(
        dut,
        [encode_i(1, 0, 0x300), encode_s(1, 2, 0, 2)],
        cause=7,
        pc=4,
        value=0x300,
        bus_errors={0x300},
    )
