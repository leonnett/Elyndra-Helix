import cocotb
from cocotb.triggers import Timer


async def tick(dut):
    dut.clk.value = 0
    await Timer(2, unit="ns")
    dut.clk.value = 1
    await Timer(2, unit="ns")
    dut.clk.value = 0
    await Timer(1, unit="ns")


@cocotb.test()
async def test_register_file_reset_write_and_x0(dut):
    dut.clk.value = 0
    dut.reset_n.value = 0
    dut.write_enable.value = 0
    dut.write_address.value = 0
    dut.write_data.value = 0
    dut.read_address_a.value = 0
    dut.read_address_b.value = 1
    await tick(dut)
    dut.reset_n.value = 1
    await Timer(1, unit="ns")
    actual = int(dut.read_data_a.value)
    assert actual == 0, f"test_register_file_reset_write_and_x0 expected x0=0 actual=0x{actual:08x}"
    actual = int(dut.read_data_b.value)
    assert actual == 0, f"test_register_file_reset_write_and_x0 expected reset x1=0 actual=0x{actual:08x}"

    dut.write_enable.value = 1
    dut.write_address.value = 9
    dut.write_data.value = 0xFEDCBA98
    await tick(dut)
    dut.write_address.value = 0
    dut.write_data.value = 0xFFFFFFFF
    dut.read_address_a.value = 9
    dut.read_address_b.value = 0
    await tick(dut)
    dut.write_enable.value = 0
    await Timer(1, unit="ns")
    actual_a = int(dut.read_data_a.value)
    actual_b = int(dut.read_data_b.value)
    assert actual_a == 0xFEDCBA98, (
        f"test_register_file_reset_write_and_x0 expected x9=0xfedcba98 actual=0x{actual_a:08x}"
    )
    assert actual_b == 0, f"test_register_file_reset_write_and_x0 expected x0=0 actual=0x{actual_b:08x}"
