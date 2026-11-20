import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_branch_conditions(dut):
    cases = [
        (0, 5, 5, 1), (0, 5, 6, 0), (1, 5, 6, 1), (1, 5, 5, 0),
        (4, 0xFFFFFFFF, 1, 1), (4, 1, 0xFFFFFFFF, 0),
        (5, 1, 0xFFFFFFFF, 1), (5, 0xFFFFFFFF, 1, 0),
        (6, 0xFFFFFFFF, 1, 0), (6, 1, 0xFFFFFFFF, 1),
        (7, 0xFFFFFFFF, 1, 1), (7, 1, 0xFFFFFFFF, 0),
    ]
    for funct3, a, b, wanted in cases:
        dut.funct3.value = funct3
        dut.a.value = a
        dut.b.value = b
        await Timer(1, unit="ns")
        actual = int(dut.taken.value)
        assert actual == wanted, (
            f"test_branch_conditions funct3={funct3} a=0x{a:08x} b=0x{b:08x} "
            f"expected={wanted} actual={actual}"
        )
