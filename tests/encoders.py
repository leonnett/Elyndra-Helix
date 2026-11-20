MASK32 = 0xFFFFFFFF


def _signed_field(value: int, width: int) -> int:
    low = -(1 << (width - 1))
    high = (1 << (width - 1)) - 1
    if not low <= value <= high:
        raise ValueError(f"immediate {value} is outside signed {width}-bit range")
    return value & ((1 << width) - 1)


def encode_r(rd: int, rs1: int, rs2: int, funct3: int, funct7: int = 0, opcode: int = 0x33) -> int:
    return ((funct7 & 0x7F) << 25) | ((rs2 & 31) << 20) | ((rs1 & 31) << 15) | ((funct3 & 7) << 12) | ((rd & 31) << 7) | (opcode & 0x7F)


def encode_i(rd: int, rs1: int, immediate: int, funct3: int = 0, opcode: int = 0x13) -> int:
    imm = _signed_field(immediate, 12)
    return (imm << 20) | ((rs1 & 31) << 15) | ((funct3 & 7) << 12) | ((rd & 31) << 7) | (opcode & 0x7F)


def encode_s(rs1: int, rs2: int, immediate: int, funct3: int) -> int:
    imm = _signed_field(immediate, 12)
    return (((imm >> 5) & 0x7F) << 25) | ((rs2 & 31) << 20) | ((rs1 & 31) << 15) | ((funct3 & 7) << 12) | ((imm & 31) << 7) | 0x23


def encode_b(rs1: int, rs2: int, offset: int, funct3: int) -> int:
    if offset & 1:
        raise ValueError("branch offset must be 2-byte aligned")
    imm = _signed_field(offset, 13)
    return (((imm >> 12) & 1) << 31) | (((imm >> 5) & 0x3F) << 25) | ((rs2 & 31) << 20) | ((rs1 & 31) << 15) | ((funct3 & 7) << 12) | (((imm >> 1) & 0xF) << 8) | (((imm >> 11) & 1) << 7) | 0x63


def encode_u(rd: int, immediate: int, opcode: int) -> int:
    return (immediate & 0xFFFFF000) | ((rd & 31) << 7) | (opcode & 0x7F)


def encode_j(rd: int, offset: int) -> int:
    if offset & 1:
        raise ValueError("jump offset must be 2-byte aligned")
    imm = _signed_field(offset, 21)
    return (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20) | (((imm >> 12) & 0xFF) << 12) | ((rd & 31) << 7) | 0x6F


def signed32(value: int) -> int:
    value &= MASK32
    return value - (1 << 32) if value & (1 << 31) else value
