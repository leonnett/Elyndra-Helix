module helix_decoder (
    input  logic [31:0] instruction,
    output logic        illegal,
    output logic        is_ecall,
    output logic        is_ebreak,
    output logic        uses_rs1,
    output logic        uses_rs2,
    output logic        reg_write,
    output logic [3:0]  alu_op,
    output logic        alu_src_imm,
    output logic        alu_src_pc,
    output logic [2:0]  immediate_kind,
    output logic        branch,
    output logic [2:0]  branch_funct3,
    output logic        jump,
    output logic        jump_reg,
    output logic        is_load,
    output logic        is_store,
    output logic [1:0]  memory_size,
    output logic        load_unsigned,
    output logic        fence_nop
);
    localparam logic [3:0] ALU_ADD  = 4'd0;
    localparam logic [3:0] ALU_SUB  = 4'd1;
    localparam logic [3:0] ALU_SLL  = 4'd2;
    localparam logic [3:0] ALU_SLT  = 4'd3;
    localparam logic [3:0] ALU_SLTU = 4'd4;
    localparam logic [3:0] ALU_XOR  = 4'd5;
    localparam logic [3:0] ALU_SRL  = 4'd6;
    localparam logic [3:0] ALU_SRA  = 4'd7;
    localparam logic [3:0] ALU_OR   = 4'd8;
    localparam logic [3:0] ALU_AND  = 4'd9;
    localparam logic [3:0] ALU_COPY_B = 4'd10;

    localparam logic [2:0] IMM_I     = 3'd0;
    localparam logic [2:0] IMM_S     = 3'd1;
    localparam logic [2:0] IMM_B     = 3'd2;
    localparam logic [2:0] IMM_U     = 3'd3;
    localparam logic [2:0] IMM_J     = 3'd4;
    localparam logic [2:0] IMM_SHIFT = 3'd5;

    logic [6:0] opcode;
    logic [2:0] funct3;
    logic [6:0] funct7;

    always_comb begin
        opcode = instruction[6:0];
        funct3 = instruction[14:12];
        funct7 = instruction[31:25];

        illegal = 1'b1;
        is_ecall = 1'b0;
        is_ebreak = 1'b0;
        uses_rs1 = 1'b0;
        uses_rs2 = 1'b0;
        reg_write = 1'b0;
        alu_op = ALU_ADD;
        alu_src_imm = 1'b0;
        alu_src_pc = 1'b0;
        immediate_kind = IMM_I;
        branch = 1'b0;
        branch_funct3 = funct3;
        jump = 1'b0;
        jump_reg = 1'b0;
        is_load = 1'b0;
        is_store = 1'b0;
        memory_size = 2'd0;
        load_unsigned = 1'b0;
        fence_nop = 1'b0;

        case (opcode)
            7'b0110011: begin // RV32I register-register integer operations
                uses_rs1 = 1'b1;
                uses_rs2 = 1'b1;
                reg_write = 1'b1;
                case ({funct7, funct3})
                    {7'b0000000, 3'b000}: begin illegal = 1'b0; alu_op = ALU_ADD;  end
                    {7'b0100000, 3'b000}: begin illegal = 1'b0; alu_op = ALU_SUB;  end
                    {7'b0000000, 3'b001}: begin illegal = 1'b0; alu_op = ALU_SLL;  end
                    {7'b0000000, 3'b010}: begin illegal = 1'b0; alu_op = ALU_SLT;  end
                    {7'b0000000, 3'b011}: begin illegal = 1'b0; alu_op = ALU_SLTU; end
                    {7'b0000000, 3'b100}: begin illegal = 1'b0; alu_op = ALU_XOR;  end
                    {7'b0000000, 3'b101}: begin illegal = 1'b0; alu_op = ALU_SRL;  end
                    {7'b0100000, 3'b101}: begin illegal = 1'b0; alu_op = ALU_SRA;  end
                    {7'b0000000, 3'b110}: begin illegal = 1'b0; alu_op = ALU_OR;   end
                    {7'b0000000, 3'b111}: begin illegal = 1'b0; alu_op = ALU_AND;  end
                    default: begin end
                endcase
            end
            7'b0010011: begin // RV32I register-immediate integer operations
                uses_rs1 = 1'b1;
                reg_write = 1'b1;
                alu_src_imm = 1'b1;
                immediate_kind = IMM_I;
                case (funct3)
                    3'b000: begin illegal = 1'b0; alu_op = ALU_ADD;  end // ADDI
                    3'b010: begin illegal = 1'b0; alu_op = ALU_SLT;  end // SLTI
                    3'b011: begin illegal = 1'b0; alu_op = ALU_SLTU; end // SLTIU
                    3'b100: begin illegal = 1'b0; alu_op = ALU_XOR;  end // XORI
                    3'b110: begin illegal = 1'b0; alu_op = ALU_OR;   end // ORI
                    3'b111: begin illegal = 1'b0; alu_op = ALU_AND;  end // ANDI
                    3'b001: begin
                        if (funct7 == 7'b0000000) begin illegal = 1'b0; alu_op = ALU_SLL; immediate_kind = IMM_SHIFT; end
                    end
                    3'b101: begin
                        if (funct7 == 7'b0000000) begin illegal = 1'b0; alu_op = ALU_SRL; immediate_kind = IMM_SHIFT; end
                        else if (funct7 == 7'b0100000) begin illegal = 1'b0; alu_op = ALU_SRA; immediate_kind = IMM_SHIFT; end
                    end
                    default: begin end
                endcase
            end
            7'b0000011: begin // Loads
                uses_rs1 = 1'b1;
                reg_write = 1'b1;
                alu_src_imm = 1'b1;
                immediate_kind = IMM_I;
                is_load = 1'b1;
                alu_op = ALU_ADD;
                case (funct3)
                    3'b000: begin illegal = 1'b0; memory_size = 2'd0; end // LB
                    3'b001: begin illegal = 1'b0; memory_size = 2'd1; end // LH
                    3'b010: begin illegal = 1'b0; memory_size = 2'd2; end // LW
                    3'b100: begin illegal = 1'b0; memory_size = 2'd0; load_unsigned = 1'b1; end // LBU
                    3'b101: begin illegal = 1'b0; memory_size = 2'd1; load_unsigned = 1'b1; end // LHU
                    default: begin end
                endcase
            end
            7'b0100011: begin // Stores
                uses_rs1 = 1'b1;
                uses_rs2 = 1'b1;
                alu_src_imm = 1'b1;
                immediate_kind = IMM_S;
                is_store = 1'b1;
                alu_op = ALU_ADD;
                case (funct3)
                    3'b000: begin illegal = 1'b0; memory_size = 2'd0; end // SB
                    3'b001: begin illegal = 1'b0; memory_size = 2'd1; end // SH
                    3'b010: begin illegal = 1'b0; memory_size = 2'd2; end // SW
                    default: begin end
                endcase
            end
            7'b1100011: begin // Conditional branches
                uses_rs1 = 1'b1;
                uses_rs2 = 1'b1;
                immediate_kind = IMM_B;
                branch = 1'b1;
                case (funct3)
                    3'b000, 3'b001, 3'b100, 3'b101, 3'b110, 3'b111: illegal = 1'b0;
                    default: begin end
                endcase
            end
            7'b1101111: begin // JAL
                illegal = 1'b0;
                reg_write = 1'b1;
                jump = 1'b1;
                immediate_kind = IMM_J;
            end
            7'b1100111: begin // JALR
                if (funct3 == 3'b000) begin
                    illegal = 1'b0;
                    uses_rs1 = 1'b1;
                    reg_write = 1'b1;
                    jump = 1'b1;
                    jump_reg = 1'b1;
                    alu_src_imm = 1'b1;
                    immediate_kind = IMM_I;
                end
            end
            7'b0110111: begin // LUI
                illegal = 1'b0;
                reg_write = 1'b1;
                alu_op = ALU_COPY_B;
                alu_src_imm = 1'b1;
                immediate_kind = IMM_U;
            end
            7'b0010111: begin // AUIPC
                illegal = 1'b0;
                reg_write = 1'b1;
                alu_src_imm = 1'b1;
                alu_src_pc = 1'b1;
                immediate_kind = IMM_U;
            end
            7'b0001111: begin // FENCE is ordered as a no-op on this serialized core
                if (funct3 == 3'b000 && instruction[31:28] == 4'b0000 &&
                    instruction[19:15] == 5'd0 && instruction[11:7] == 5'd0) begin
                    illegal = 1'b0;
                    fence_nop = 1'b1;
                end
            end
            7'b1110011: begin // ECALL and EBREAK only; no CSR or privileged ISA
                if (funct3 == 3'b000 && instruction[19:15] == 5'd0 && instruction[11:7] == 5'd0) begin
                    if (instruction[31:20] == 12'h000) begin
                        illegal = 1'b0;
                        is_ecall = 1'b1;
                    end else if (instruction[31:20] == 12'h001) begin
                        illegal = 1'b0;
                        is_ebreak = 1'b1;
                    end
                end
            end
            default: begin end
        endcase
    end
endmodule
