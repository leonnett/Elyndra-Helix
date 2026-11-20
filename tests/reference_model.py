from dataclasses import dataclass

from encoders import MASK32, signed32


@dataclass
class Commit:
    pc: int
    instruction: int
    rd_write: bool = False
    rd: int = 0
    rd_data: int = 0
    mem_access: bool = False
    mem_write: bool = False
    mem_address: int = 0
    mem_strobes: int = 0
    mem_data: int = 0


class ReferenceTrap(Exception):
    def __init__(self, cause: int, pc: int, value: int = 0):
        self.cause = cause
        self.pc = pc
        self.value = value & MASK32
        super().__init__(f"trap cause={cause} pc=0x{pc:08x} value=0x{self.value:08x}")


class RV32IReference:
    """Small architectural interpreter; it models ISA state, not the RTL datapath."""

    def __init__(self, memory: bytearray, reset_pc: int = 0):
        self.memory = bytearray(memory)
        self.regs = [0] * 32
        self.pc = reset_pc & MASK32

    @staticmethod
    def _sext(value: int, bits: int) -> int:
        sign = 1 << (bits - 1)
        return ((value ^ sign) - sign) & MASK32

    def _read(self, address: int, size: int, unsigned: bool) -> int:
        if address + size > len(self.memory):
            raise ReferenceTrap(5, self.pc, address)
        if size > 1 and address % size:
            raise ReferenceTrap(4, self.pc, address)
        value = int.from_bytes(self.memory[address : address + size], "little")
        if unsigned:
            return value
        return self._sext(value, size * 8)

    def _write(self, address: int, size: int, value: int) -> tuple[int, int]:
        if address + size > len(self.memory):
            raise ReferenceTrap(7, self.pc, address)
        if size > 1 and address % size:
            raise ReferenceTrap(6, self.pc, address)
        mask = ((1 << size) - 1) << (address & 3)
        bus_data = (value << (8 * (address & 3))) & MASK32
        self.memory[address : address + size] = (value & ((1 << (size * 8)) - 1)).to_bytes(size, "little")
        return mask, bus_data

    def step(self, instruction: int) -> Commit:
        pc = self.pc
        instruction &= MASK32
        opcode = instruction & 0x7F
        rd = (instruction >> 7) & 31
        funct3 = (instruction >> 12) & 7
        rs1 = (instruction >> 15) & 31
        rs2 = (instruction >> 20) & 31
        funct7 = (instruction >> 25) & 0x7F
        a = self.regs[rs1]
        b = self.regs[rs2]
        imm_i = self._sext(instruction >> 20, 12)
        imm_s = self._sext(((instruction >> 25) << 5) | ((instruction >> 7) & 31), 12)
        imm_b = self._sext((((instruction >> 31) & 1) << 12) | (((instruction >> 7) & 1) << 11) | (((instruction >> 25) & 0x3F) << 5) | (((instruction >> 8) & 0xF) << 1), 13)
        imm_u = instruction & 0xFFFFF000
        imm_j = self._sext((((instruction >> 31) & 1) << 20) | (((instruction >> 12) & 0xFF) << 12) | (((instruction >> 20) & 1) << 11) | (((instruction >> 21) & 0x3FF) << 1), 21)
        next_pc = (pc + 4) & MASK32
        result = 0
        write_rd = False
        mem_access = False
        mem_write = False
        mem_address = 0
        mem_strobes = 0
        mem_data = 0

        if opcode == 0x33:
            write_rd = True
            if funct7 == 0 and funct3 == 0:
                result = a + b
            elif funct7 == 0x20 and funct3 == 0:
                result = a - b
            elif funct7 == 0 and funct3 == 1:
                result = a << (b & 31)
            elif funct7 == 0 and funct3 == 2:
                result = int(signed32(a) < signed32(b))
            elif funct7 == 0 and funct3 == 3:
                result = int(a < b)
            elif funct7 == 0 and funct3 == 4:
                result = a ^ b
            elif funct7 == 0 and funct3 == 5:
                result = a >> (b & 31)
            elif funct7 == 0x20 and funct3 == 5:
                result = signed32(a) >> (b & 31)
            elif funct7 == 0 and funct3 == 6:
                result = a | b
            elif funct7 == 0 and funct3 == 7:
                result = a & b
            else:
                raise ReferenceTrap(2, pc, instruction)
        elif opcode == 0x13:
            write_rd = True
            if funct3 == 0:
                result = a + signed32(imm_i)
            elif funct3 == 2:
                result = int(signed32(a) < signed32(imm_i))
            elif funct3 == 3:
                result = int(a < imm_i)
            elif funct3 == 4:
                result = a ^ imm_i
            elif funct3 == 6:
                result = a | imm_i
            elif funct3 == 7:
                result = a & imm_i
            elif funct3 == 1 and funct7 == 0:
                result = a << rs2
            elif funct3 == 5 and funct7 == 0:
                result = a >> rs2
            elif funct3 == 5 and funct7 == 0x20:
                result = signed32(a) >> rs2
            else:
                raise ReferenceTrap(2, pc, instruction)
        elif opcode == 0x03:
            width_by_funct = {0: (1, False), 1: (2, False), 2: (4, False), 4: (1, True), 5: (2, True)}
            if funct3 not in width_by_funct:
                raise ReferenceTrap(2, pc, instruction)
            size, unsigned = width_by_funct[funct3]
            address = (a + signed32(imm_i)) & MASK32
            result = self._read(address, size, unsigned)
            write_rd = True
            mem_access = True
            mem_address = address
        elif opcode == 0x23:
            width_by_funct = {0: 1, 1: 2, 2: 4}
            if funct3 not in width_by_funct:
                raise ReferenceTrap(2, pc, instruction)
            size = width_by_funct[funct3]
            address = (a + signed32(imm_s)) & MASK32
            mem_strobes, mem_data = self._write(address, size, b)
            mem_access = True
            mem_write = True
            mem_address = address
        elif opcode == 0x63:
            condition = {
                0: a == b,
                1: a != b,
                4: signed32(a) < signed32(b),
                5: signed32(a) >= signed32(b),
                6: a < b,
                7: a >= b,
            }.get(funct3)
            if condition is None:
                raise ReferenceTrap(2, pc, instruction)
            if condition:
                next_pc = (pc + signed32(imm_b)) & MASK32
        elif opcode == 0x6F:
            write_rd = True
            result = next_pc
            next_pc = (pc + signed32(imm_j)) & MASK32
        elif opcode == 0x67 and funct3 == 0:
            write_rd = True
            result = next_pc
            next_pc = ((a + signed32(imm_i)) & MASK32) & ~1
        elif opcode == 0x37:
            write_rd = True
            result = imm_u
        elif opcode == 0x17:
            write_rd = True
            result = pc + imm_u
        elif opcode == 0x0F and funct3 == 0 and ((instruction >> 28) & 0xF) == 0 and rs1 == 0 and rd == 0:
            pass  # FENCE is ordered by the single outstanding transaction interface.
        elif opcode == 0x73 and funct3 == 0 and rs1 == 0 and rd == 0:
            imm12 = (instruction >> 20) & 0xFFF
            if imm12 == 0:
                raise ReferenceTrap(11, pc)
            if imm12 == 1:
                raise ReferenceTrap(3, pc)
            raise ReferenceTrap(2, pc, instruction)
        else:
            raise ReferenceTrap(2, pc, instruction)

        if next_pc & 3:
            raise ReferenceTrap(0, pc, next_pc)
        result &= MASK32
        if write_rd and rd != 0:
            self.regs[rd] = result
        self.regs[0] = 0
        self.pc = next_pc
        return Commit(
            pc=pc,
            instruction=instruction,
            rd_write=write_rd and rd != 0,
            rd=rd,
            rd_data=result,
            mem_access=mem_access,
            mem_write=mem_write,
            mem_address=mem_address,
            mem_strobes=mem_strobes,
            mem_data=mem_data,
        )
