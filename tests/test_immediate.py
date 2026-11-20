import cocotb
from cocotb.triggers import Timer

from encoders import encode_b, encode_i, encode_j, encode_s, encode_u


@cocotb.test()
async def test_immediate_formats(dut):
    vectors = [
        (0, encode_i(1, 2, -17), 0xFFFFFFEF),
        (1, encode_s(2, 3, -32, 2), 0xFFFFFFE0),
        (2, encode_b(2, 3, -16, 0), 0xFFFFFFF0),
        (3, encode_u(1, 0xABCDE000, 0x37), 0xABCDE000),
        (4, encode_j(1, -2048), 0xFFFFF800),
        (5, encode_i(1, 2, 31, 1), 31),
    ]
    for kind, instruction, wanted in vectors:
        dut.immediate_kind.value = kind
        dut.instruction.value = instruction
        await Timer(1, unit="ns")
        actual = int(dut.immediate.value)
        assert actual == wanted, (
            f"test_immediate_formats kind={kind} instruction=0x{instruction:08x} "
            f"expected=0x{wanted:08x} actual=0x{actual:08x}"
        )
