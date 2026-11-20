from encoders import encode_b, encode_i, encode_j, encode_r, encode_s, encode_u


class ProgramBuilder:
    def __init__(self) -> None:
        self.words: list[int | tuple[str, tuple[int, ...], str]] = []
        self.labels: dict[str, int] = {}

    def emit(self, instruction: int) -> None:
        self.words.append(instruction & 0xFFFFFFFF)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = len(self.words) * 4

    def branch(self, name: str, rs1: int, rs2: int, funct3: int) -> None:
        self.words.append(("branch", (rs1, rs2, funct3), name))

    def jal(self, name: str, rd: int) -> None:
        self.words.append(("jal", (rd,), name))

    def jalr(self, name: str, rd: int) -> None:
        self.words.append(("jalr", (rd,), name))

    def finish(self) -> list[int]:
        result: list[int] = []
        for index, entry in enumerate(self.words):
            if isinstance(entry, int):
                result.append(entry)
                continue
            kind, operands, target_name = entry
            if target_name not in self.labels:
                raise ValueError(f"undefined label: {target_name}")
            pc = index * 4
            target = self.labels[target_name]
            if kind == "branch":
                result.append(encode_b(operands[0], operands[1], target - pc, operands[2]))
            elif kind == "jal":
                result.append(encode_j(operands[0], target - pc))
            elif kind == "jalr":
                result.append(encode_i(operands[0], 0, target, funct3=0, opcode=0x67))
            else:
                raise ValueError(f"unknown fixup: {kind}")
        return result


def build_rv32i_smoke() -> list[int]:
    p = ProgramBuilder()
    # Register-register arithmetic and logical operations.
    p.emit(encode_i(1, 0, 5))
    p.emit(encode_i(2, 0, 7))
    p.emit(encode_r(3, 1, 2, 0))
    p.emit(encode_r(4, 1, 2, 0, 0x20))
    p.emit(encode_r(5, 1, 2, 1))
    p.emit(encode_r(6, 4, 2, 2))
    p.emit(encode_r(7, 4, 2, 3))
    p.emit(encode_r(8, 1, 2, 4))
    p.emit(encode_r(9, 5, 1, 5))
    p.emit(encode_r(10, 4, 1, 5, 0x20))
    p.emit(encode_r(11, 1, 2, 6))
    p.emit(encode_r(12, 1, 2, 7))

    # Immediate arithmetic, shifts, and upper-immediate operations.
    p.emit(encode_i(13, 1, -3))
    p.emit(encode_i(14, 4, -1, 2))
    p.emit(encode_i(15, 0, -1, 3))
    p.emit(encode_i(16, 1, 0x55, 4))
    p.emit(encode_i(17, 1, 0x10, 6))
    p.emit(encode_i(18, 17, 7, 7))
    p.emit(encode_i(19, 1, 3, 1))
    p.emit(encode_i(20, 19, 2, 5))
    p.emit(encode_i(21, 4, (0x400 | 1), 5))  # SRAI funct7=0100000, shamt=1.
    p.emit(encode_u(22, 0x12345000, 0x37))
    p.emit(encode_u(23, 0x00001000, 0x17))

    # Byte-addressed memory operations at 0x300.
    p.emit(encode_i(24, 0, 0x300))
    p.emit(encode_s(24, 3, 0, 2))
    p.emit(encode_i(25, 24, 0, 0, 0x03))
    p.emit(encode_i(26, 24, 0, 4, 0x03))
    p.emit(encode_s(24, 1, 4, 1))
    p.emit(encode_i(27, 24, 4, 1, 0x03))
    p.emit(encode_i(28, 24, 4, 5, 0x03))
    p.emit(encode_s(24, 4, 8, 1))
    p.emit(encode_i(27, 24, 8, 1, 0x03))
    p.emit(encode_i(28, 24, 8, 5, 0x03))
    p.emit(encode_s(24, 4, 6, 0))
    p.emit(encode_i(30, 24, 6, 4, 0x03))
    p.emit(encode_i(29, 24, 6, 0, 0x03))

    # All six branch comparisons, with taken and not-taken paths.
    p.emit(encode_i(30, 0, 1))
    p.branch("beq_taken", 30, 30, 0)
    p.emit(encode_i(31, 0, 99))
    p.label("beq_taken")
    p.branch("bne_taken", 30, 0, 1)
    p.emit(encode_i(31, 0, 98))
    p.label("bne_taken")
    p.branch("blt_taken", 4, 2, 4)
    p.emit(encode_i(31, 0, 97))
    p.label("blt_taken")
    p.branch("bge_taken", 2, 4, 5)
    p.emit(encode_i(31, 0, 96))
    p.label("bge_taken")
    p.branch("bltu_not_taken", 4, 2, 6)
    p.label("bltu_not_taken")
    p.branch("bgeu_taken", 4, 2, 7)
    p.emit(encode_i(31, 0, 95))
    p.label("bgeu_taken")
    p.branch("beq_not_taken", 30, 0, 0)
    p.label("beq_not_taken")
    p.branch("bne_not_taken", 30, 30, 1)
    p.label("bne_not_taken")

    # Direct and register-indirect jumps skip sentinel instructions.
    p.jal("jal_target", 5)
    p.emit(encode_i(31, 0, 94))
    p.label("jal_target")
    p.jalr("jalr_target", 6)
    p.emit(encode_i(31, 0, 93))
    p.label("jalr_target")
    p.emit(0x0000000F)  # FENCE; prior memory operations have completed in-order.
    p.emit(0x00100073)  # EBREAK terminates the program through the visible trap interface.
    return p.finish()
