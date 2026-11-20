import os
import random

import cocotb
from cocotb.triggers import Timer

from encoders import MASK32, signed32


def expected(op: int, a: int, b: int) -> int:
    shift = b & 31
    if op == 0:
        value = a + b
    elif op == 1:
        value = a - b
    elif op == 2:
        value = a << shift
    elif op == 3:
        value = int(signed32(a) < signed32(b))
    elif op == 4:
        value = int(a < b)
    elif op == 5:
        value = a ^ b
    elif op == 6:
        value = a >> shift
    elif op == 7:
        value = signed32(a) >> shift
    elif op == 8:
        value = a | b
    elif op == 9:
        value = a & b
    elif op == 10:
        value = b
    else:
        value = 0
    return value & MASK32


@cocotb.test()
async def test_alu_directed_and_seeded_random(dut):
    seed = int(os.environ.get("HELIX_SEED", "1212231729"), 0)
    rng = random.Random(seed)
    vectors = [
        (0, 0, 0), (0, 0xFFFFFFFF, 1), (1, 0, 1), (1, 0, 0xFFFFFFFF),
        (2, 1, 31), (2, 0x80000001, 1), (3, 0xFFFFFFFF, 0),
        (4, 0xFFFFFFFF, 0), (5, 0xA55A00FF, 0x0FF00F0F),
        (6, 0x80000000, 31), (7, 0x80000000, 1), (8, 0xAA00, 0x55),
        (9, 0xFFFF, 0x0F0F), (10, 0, 0xFEDCBA98),
    ]
    vectors.extend((op, rng.getrandbits(32), rng.getrandbits(32)) for op in range(11) for _ in range(64))
    for index, (op, a, b) in enumerate(vectors):
        dut.op.value = op
        dut.a.value = a
        dut.b.value = b
        await Timer(1, unit="ns")
        actual = int(dut.result.value)
        wanted = expected(op, a, b)
        assert actual == wanted, (
            f"test_alu_directed_and_seeded_random seed={seed} vector={index} "
            f"instruction=alu_op:{op} inputs={{a:0x{a:08x},b:0x{b:08x}}} "
            f"expected=0x{wanted:08x} actual=0x{actual:08x}"
        )
