import cocotb
from cocotb.triggers import Timer

from encoders import encode_b, encode_i, encode_r, encode_s, encode_u


@cocotb.test()
async def test_decoder_instruction_classes_and_illegal_encodings(dut):
    vectors = [
        (encode_r(3, 1, 2, 0), 0, 0, 0, 0, 0),
        (encode_r(3, 1, 2, 0, 0x20), 0, 0, 0, 0, 0),
        (encode_i(3, 1, -4, 0), 0, 0, 0, 0, 0),
        (encode_i(3, 1, 6, 5), 0, 0, 0, 0, 0),
        (encode_i(3, 1, 1, 0, 0x03), 0, 0, 1, 0, 0),
        (encode_s(1, 2, 4, 2), 0, 0, 0, 1, 0),
        (encode_b(1, 2, 8, 4), 0, 0, 0, 0, 0),
        (encode_u(3, 0x12345000, 0x37), 0, 0, 0, 0, 0),
        (0x0000000F, 0, 0, 0, 0, 1),
        (0x00000073, 0, 1, 0, 0, 0),
        (0x00100073, 0, 0, 0, 0, 0),
        (0xFFFFFFFF, 1, 0, 0, 0, 0),
        (0x0000100F, 1, 0, 0, 0, 0),
        (encode_r(3, 1, 2, 0, 1), 1, 0, 0, 0, 0),
        (encode_i(3, 1, 1, 1, 0x67), 1, 0, 0, 0, 0),
    ]
    for instruction, illegal, ecall, is_load, is_store, fence in vectors:
        dut.instruction.value = instruction
        await Timer(1, unit="ns")
        actuals = (
            int(dut.illegal.value), int(dut.is_ecall.value), int(dut.is_load.value),
            int(dut.is_store.value), int(dut.fence_nop.value),
        )
        wanted = (illegal, ecall, is_load, is_store, fence)
        assert actuals == wanted, (
            f"test_decoder instruction=0x{instruction:08x} expected={wanted} actual={actuals}"
        )

    dut.instruction.value = 0x00100073
    await Timer(1, unit="ns")
    actual_ebreak = int(dut.is_ebreak.value)
    assert actual_ebreak == 1, f"test_decoder_instruction_classes expected_ebreak=1 actual={actual_ebreak}"
