module helix_core #(
    parameter integer EXEC_CONFIG = 0,
    parameter logic [31:0] RESET_PC = 32'h0000_0000
) (
    input  logic        clk,
    input  logic        reset_n,

    output logic        mem_valid,
    output logic        mem_write,
    output logic [31:0] mem_address,
    output logic [31:0] mem_write_data,
    output logic [3:0]  mem_write_strobes,
    input  logic [31:0] mem_read_data,
    input  logic        mem_ready,
    input  logic        mem_error,

    output logic        retire_valid,
    output logic [31:0] retire_pc,
    output logic [31:0] retire_instruction,
    output logic        retire_rd_write,
    output logic [4:0]  retire_rd,
    output logic [31:0] retire_rd_data,
    output logic        retire_mem_access,
    output logic        retire_mem_write,
    output logic [31:0] retire_mem_address,
    output logic [3:0]  retire_mem_strobes,
    output logic [31:0] retire_mem_data,

    output logic        trap_valid,
    output logic [31:0] trap_cause,
    output logic [31:0] trap_pc,
    output logic [31:0] trap_value,
    output logic [2:0]  debug_state
);
    localparam logic [2:0] STATE_FETCH     = 3'd0;
    localparam logic [2:0] STATE_DECODE    = 3'd1;
    localparam logic [2:0] STATE_PREPARE   = 3'd2;
    localparam logic [2:0] STATE_EXECUTE   = 3'd3;
    localparam logic [2:0] STATE_MEMORY    = 3'd4;
    localparam logic [2:0] STATE_WRITEBACK = 3'd5;
    localparam logic [2:0] STATE_HALTED    = 3'd6;

    localparam logic [31:0] CAUSE_INSTRUCTION_ADDRESS_MISALIGNED = 32'd0;
    localparam logic [31:0] CAUSE_INSTRUCTION_ACCESS_FAULT = 32'd1;
    localparam logic [31:0] CAUSE_ILLEGAL_INSTRUCTION = 32'd2;
    localparam logic [31:0] CAUSE_BREAKPOINT = 32'd3;
    localparam logic [31:0] CAUSE_LOAD_ADDRESS_MISALIGNED = 32'd4;
    localparam logic [31:0] CAUSE_LOAD_ACCESS_FAULT = 32'd5;
    localparam logic [31:0] CAUSE_STORE_ADDRESS_MISALIGNED = 32'd6;
    localparam logic [31:0] CAUSE_STORE_ACCESS_FAULT = 32'd7;
    localparam logic [31:0] CAUSE_ENVIRONMENT_CALL = 32'd11;

    logic [2:0] state_q;
    logic [2:0] state_d;
    logic [31:0] pc_q;
    logic [31:0] instruction_q;
    logic [31:0] instruction_pc_q;

    logic [31:0] source_a_q;
    logic [31:0] source_b_q;
    logic [31:0] immediate_q;
    logic [31:0] execute_pc_q;
    logic [31:0] execute_instruction_q;
    logic [4:0] destination_q;
    logic [3:0] alu_operation_q;
    logic       alu_source_immediate_q;
    logic       alu_source_pc_q;
    logic       reg_write_q;
    logic       branch_q;
    logic [2:0] branch_funct3_q;
    logic       jump_q;
    logic       jump_register_q;
    logic       load_q;
    logic       store_q;
    logic [1:0] memory_size_q;
    logic       load_unsigned_q;

    logic [31:0] prepared_source_a_q;
    logic [31:0] prepared_source_b_q;
    logic [31:0] prepared_immediate_q;
    logic [31:0] prepared_pc_q;
    logic [31:0] prepared_instruction_q;
    logic [4:0]  prepared_destination_q;
    logic [3:0]  prepared_alu_operation_q;
    logic        prepared_alu_source_immediate_q;
    logic        prepared_alu_source_pc_q;
    logic        prepared_reg_write_q;
    logic        prepared_branch_q;
    logic [2:0]  prepared_branch_funct3_q;
    logic        prepared_jump_q;
    logic        prepared_jump_register_q;
    logic        prepared_load_q;
    logic        prepared_store_q;
    logic [1:0]  prepared_memory_size_q;
    logic        prepared_load_unsigned_q;

    logic [31:0] writeback_data_q;
    logic [31:0] effective_address_q;
    logic [31:0] store_data_q;
    logic [1:0] pending_memory_size_q;
    logic       pending_load_unsigned_q;

    logic decoder_illegal;
    logic decoder_ecall;
    logic decoder_ebreak;
    logic decoder_uses_rs1;
    logic decoder_uses_rs2;
    logic decoder_reg_write;
    logic [3:0] decoder_alu_operation;
    logic decoder_alu_source_immediate;
    logic decoder_alu_source_pc;
    logic [2:0] decoder_immediate_kind;
    logic decoder_branch;
    logic [2:0] decoder_branch_funct3;
    logic decoder_jump;
    logic decoder_jump_register;
    logic decoder_load;
    logic decoder_store;
    logic [1:0] decoder_memory_size;
    logic decoder_load_unsigned;
    logic decoder_fence_nop;
    logic [31:0] decoded_immediate;

    logic [31:0] register_data_a;
    logic [31:0] register_data_b;
    logic [31:0] alu_operand_a;
    logic [31:0] alu_operand_b;
    logic [31:0] alu_result;
    logic [31:0] flow_target;
    logic flow_taken;
    logic branch_taken;
    logic execute_exception;
    logic execute_memory_operation;
    logic memory_misaligned;
    logic [31:0] memory_effective_address;
    logic [1:0] memory_access_size;
    logic [31:0] formatted_load_data;
    logic [31:0] bus_aligned_address;
    logic [3:0] bus_strobes;
    logic [31:0] bus_formatted_store_data;
    logic fetch_accept;
    logic memory_accept;
    logic decode_exception;
    logic [31:0] execute_writeback_data;
    logic execute_register_write;
    logic register_write_enable;
    logic [4:0] register_write_address;
    logic [31:0] register_write_data;
    logic [31:0] trap_cause_q;
    logic [31:0] trap_pc_q;
    logic [31:0] trap_value_q;

    assign debug_state = state_q;
    assign trap_cause = trap_cause_q;
    assign trap_pc = trap_pc_q;
    assign trap_value = trap_value_q;
    assign decode_exception = decoder_illegal || decoder_ecall || decoder_ebreak;
    assign fetch_accept = (state_q == STATE_FETCH) && mem_ready;
    assign memory_accept = (state_q == STATE_MEMORY) && mem_ready;
    assign execute_memory_operation = load_q || store_q;

    helix_decoder u_decoder (
        .instruction(instruction_q),
        .illegal(decoder_illegal),
        .is_ecall(decoder_ecall),
        .is_ebreak(decoder_ebreak),
        .uses_rs1(decoder_uses_rs1),
        .uses_rs2(decoder_uses_rs2),
        .reg_write(decoder_reg_write),
        .alu_op(decoder_alu_operation),
        .alu_src_imm(decoder_alu_source_immediate),
        .alu_src_pc(decoder_alu_source_pc),
        .immediate_kind(decoder_immediate_kind),
        .branch(decoder_branch),
        .branch_funct3(decoder_branch_funct3),
        .jump(decoder_jump),
        .jump_reg(decoder_jump_register),
        .is_load(decoder_load),
        .is_store(decoder_store),
        .memory_size(decoder_memory_size),
        .load_unsigned(decoder_load_unsigned),
        .fence_nop(decoder_fence_nop)
    );

    helix_immediate u_immediate (
        .instruction(instruction_q),
        .immediate_kind(decoder_immediate_kind),
        .immediate(decoded_immediate)
    );

    helix_register_file u_register_file (
        .clk(clk),
        .reset_n(reset_n),
        .write_enable(register_write_enable),
        .write_address(register_write_address),
        .write_data(register_write_data),
        .read_address_a(instruction_q[19:15]),
        .read_address_b(instruction_q[24:20]),
        .read_data_a(register_data_a),
        .read_data_b(register_data_b)
    );

    helix_execution_fabric #(.CONFIGURATION(EXEC_CONFIG)) u_execution_fabric (
        .operand_a(alu_operand_a),
        .operand_b(alu_operand_b),
        .operation(alu_operation_q),
        .result(alu_result)
    );

    helix_branch u_branch (
        .funct3(branch_funct3_q),
        .a(source_a_q),
        .b(source_b_q),
        .taken(branch_taken)
    );

    helix_memory_interface u_memory_interface (
        .effective_address(memory_effective_address),
        .access_size(memory_access_size),
        .load_unsigned((state_q == STATE_EXECUTE) ? load_unsigned_q : pending_load_unsigned_q),
        .store_data((state_q == STATE_EXECUTE) ? source_b_q : store_data_q),
        .bus_read_data(mem_read_data),
        .misaligned(memory_misaligned),
        .bus_address(bus_aligned_address),
        .bus_write_strobes(bus_strobes),
        .bus_write_data(bus_formatted_store_data),
        .load_result(formatted_load_data)
    );

    helix_control u_control (
        .state(state_q),
        .decoupled_configuration(EXEC_CONFIG == 2),
        .fetch_accept(fetch_accept),
        .fetch_error(mem_error),
        .decode_exception(decode_exception),
        .execute_exception(execute_exception),
        .execute_memory_operation(execute_memory_operation),
        .memory_accept(memory_accept),
        .memory_error(mem_error),
        .memory_is_load(load_q),
        .next_state(state_d)
    );

    always_comb begin
        alu_operand_a = alu_source_pc_q ? execute_pc_q : source_a_q;
        alu_operand_b = alu_source_immediate_q ? immediate_q : source_b_q;
        flow_taken = jump_q || (branch_q && branch_taken);
        if (jump_register_q)
            flow_target = (source_a_q + immediate_q) & 32'hffff_fffe;
        else
            flow_target = execute_pc_q + immediate_q;

        memory_effective_address = (state_q == STATE_EXECUTE) ? alu_result : effective_address_q;
        memory_access_size = (state_q == STATE_EXECUTE) ? memory_size_q : pending_memory_size_q;
        execute_exception = 1'b0;
        if ((state_q == STATE_EXECUTE) && flow_taken && (flow_target[1:0] != 2'b00))
            execute_exception = 1'b1;
        if ((state_q == STATE_EXECUTE) && execute_memory_operation && memory_misaligned)
            execute_exception = 1'b1;

        execute_writeback_data = jump_q ? (execute_pc_q + 32'd4) : alu_result;
        execute_register_write = reg_write_q && !load_q && !store_q;
        register_write_enable = 1'b0;
        register_write_address = destination_q;
        register_write_data = execute_writeback_data;
        if (state_q == STATE_EXECUTE && execute_register_write && !execute_exception) begin
            register_write_enable = 1'b1;
        end else if (state_q == STATE_WRITEBACK) begin
            register_write_enable = 1'b1;
            register_write_data = writeback_data_q;
        end

        mem_valid = (state_q == STATE_FETCH) || (state_q == STATE_MEMORY);
        mem_write = (state_q == STATE_MEMORY) && !load_q;
        if (state_q == STATE_FETCH) begin
            mem_address = pc_q;
            mem_write_data = 32'd0;
            mem_write_strobes = 4'b0000;
        end else begin
            mem_address = bus_aligned_address;
            mem_write_data = bus_formatted_store_data;
            mem_write_strobes = store_q ? bus_strobes : 4'b0000;
        end
    end

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            state_q <= STATE_FETCH;
            pc_q <= RESET_PC;
            instruction_q <= 32'd0;
            instruction_pc_q <= RESET_PC;
            source_a_q <= 32'd0;
            source_b_q <= 32'd0;
            immediate_q <= 32'd0;
            execute_pc_q <= RESET_PC;
            execute_instruction_q <= 32'd0;
            destination_q <= 5'd0;
            alu_operation_q <= 4'd0;
            alu_source_immediate_q <= 1'b0;
            alu_source_pc_q <= 1'b0;
            reg_write_q <= 1'b0;
            branch_q <= 1'b0;
            branch_funct3_q <= 3'd0;
            jump_q <= 1'b0;
            jump_register_q <= 1'b0;
            load_q <= 1'b0;
            store_q <= 1'b0;
            memory_size_q <= 2'd0;
            load_unsigned_q <= 1'b0;
            prepared_source_a_q <= 32'd0;
            prepared_source_b_q <= 32'd0;
            prepared_immediate_q <= 32'd0;
            prepared_pc_q <= RESET_PC;
            prepared_instruction_q <= 32'd0;
            prepared_destination_q <= 5'd0;
            prepared_alu_operation_q <= 4'd0;
            prepared_alu_source_immediate_q <= 1'b0;
            prepared_alu_source_pc_q <= 1'b0;
            prepared_reg_write_q <= 1'b0;
            prepared_branch_q <= 1'b0;
            prepared_branch_funct3_q <= 3'd0;
            prepared_jump_q <= 1'b0;
            prepared_jump_register_q <= 1'b0;
            prepared_load_q <= 1'b0;
            prepared_store_q <= 1'b0;
            prepared_memory_size_q <= 2'd0;
            prepared_load_unsigned_q <= 1'b0;
            writeback_data_q <= 32'd0;
            effective_address_q <= 32'd0;
            store_data_q <= 32'd0;
            pending_memory_size_q <= 2'd0;
            pending_load_unsigned_q <= 1'b0;
            retire_valid <= 1'b0;
            retire_pc <= 32'd0;
            retire_instruction <= 32'd0;
            retire_rd_write <= 1'b0;
            retire_rd <= 5'd0;
            retire_rd_data <= 32'd0;
            retire_mem_access <= 1'b0;
            retire_mem_write <= 1'b0;
            retire_mem_address <= 32'd0;
            retire_mem_strobes <= 4'd0;
            retire_mem_data <= 32'd0;
            trap_valid <= 1'b0;
            trap_cause_q <= 32'd0;
            trap_pc_q <= 32'd0;
            trap_value_q <= 32'd0;
        end else begin
            state_q <= state_d;
            retire_valid <= 1'b0;
            retire_rd_write <= 1'b0;
            retire_rd <= 5'd0;
            retire_rd_data <= 32'd0;
            retire_mem_access <= 1'b0;
            retire_mem_write <= 1'b0;
            retire_mem_strobes <= 4'd0;
            retire_mem_data <= 32'd0;

            case (state_q)
                STATE_FETCH: begin
                    if (mem_ready) begin
                        if (mem_error) begin
                            trap_valid <= 1'b1;
                            trap_cause_q <= CAUSE_INSTRUCTION_ACCESS_FAULT;
                            trap_pc_q <= pc_q;
                            trap_value_q <= pc_q;
                        end else begin
                            instruction_q <= mem_read_data;
                            instruction_pc_q <= pc_q;
                            pc_q <= pc_q + 32'd4;
                        end
                    end
                end
                STATE_DECODE: begin
                    if (decoder_illegal || decoder_ecall || decoder_ebreak) begin
                        trap_valid <= 1'b1;
                        if (decoder_ecall)
                            trap_cause_q <= CAUSE_ENVIRONMENT_CALL;
                        else if (decoder_ebreak)
                            trap_cause_q <= CAUSE_BREAKPOINT;
                        else
                            trap_cause_q <= CAUSE_ILLEGAL_INSTRUCTION;
                        trap_pc_q <= instruction_pc_q;
                        trap_value_q <= decoder_illegal ? instruction_q : 32'd0;
                    end else if (EXEC_CONFIG == 2) begin
                        prepared_source_a_q <= decoder_uses_rs1 ? register_data_a : 32'd0;
                        prepared_source_b_q <= decoder_uses_rs2 ? register_data_b : 32'd0;
                        prepared_immediate_q <= decoded_immediate;
                        prepared_pc_q <= instruction_pc_q;
                        prepared_instruction_q <= instruction_q;
                        prepared_destination_q <= instruction_q[11:7];
                        prepared_alu_operation_q <= decoder_alu_operation;
                        prepared_alu_source_immediate_q <= decoder_alu_source_immediate;
                        prepared_alu_source_pc_q <= decoder_alu_source_pc;
                        prepared_reg_write_q <= decoder_reg_write;
                        prepared_branch_q <= decoder_branch;
                        prepared_branch_funct3_q <= decoder_branch_funct3;
                        prepared_jump_q <= decoder_jump;
                        prepared_jump_register_q <= decoder_jump_register;
                        prepared_load_q <= decoder_load;
                        prepared_store_q <= decoder_store;
                        prepared_memory_size_q <= decoder_memory_size;
                        prepared_load_unsigned_q <= decoder_load_unsigned;
                    end else begin
                        source_a_q <= decoder_uses_rs1 ? register_data_a : 32'd0;
                        source_b_q <= decoder_uses_rs2 ? register_data_b : 32'd0;
                        immediate_q <= decoded_immediate;
                        execute_pc_q <= instruction_pc_q;
                        execute_instruction_q <= instruction_q;
                        destination_q <= instruction_q[11:7];
                        alu_operation_q <= decoder_alu_operation;
                        alu_source_immediate_q <= decoder_alu_source_immediate;
                        alu_source_pc_q <= decoder_alu_source_pc;
                        reg_write_q <= decoder_reg_write;
                        branch_q <= decoder_branch;
                        branch_funct3_q <= decoder_branch_funct3;
                        jump_q <= decoder_jump;
                        jump_register_q <= decoder_jump_register;
                        load_q <= decoder_load;
                        store_q <= decoder_store;
                        memory_size_q <= decoder_memory_size;
                        load_unsigned_q <= decoder_load_unsigned;
                    end
                end
                STATE_PREPARE: begin
                    source_a_q <= prepared_source_a_q;
                    source_b_q <= prepared_source_b_q;
                    immediate_q <= prepared_immediate_q;
                    execute_pc_q <= prepared_pc_q;
                    execute_instruction_q <= prepared_instruction_q;
                    destination_q <= prepared_destination_q;
                    alu_operation_q <= prepared_alu_operation_q;
                    alu_source_immediate_q <= prepared_alu_source_immediate_q;
                    alu_source_pc_q <= prepared_alu_source_pc_q;
                    reg_write_q <= prepared_reg_write_q;
                    branch_q <= prepared_branch_q;
                    branch_funct3_q <= prepared_branch_funct3_q;
                    jump_q <= prepared_jump_q;
                    jump_register_q <= prepared_jump_register_q;
                    load_q <= prepared_load_q;
                    store_q <= prepared_store_q;
                    memory_size_q <= prepared_memory_size_q;
                    load_unsigned_q <= prepared_load_unsigned_q;
                end
                STATE_EXECUTE: begin
                    if (execute_exception) begin
                        trap_valid <= 1'b1;
                        if (execute_memory_operation && memory_misaligned) begin
                            trap_cause_q <= load_q ? CAUSE_LOAD_ADDRESS_MISALIGNED : CAUSE_STORE_ADDRESS_MISALIGNED;
                            trap_value_q <= alu_result;
                        end else begin
                            trap_cause_q <= CAUSE_INSTRUCTION_ADDRESS_MISALIGNED;
                            trap_value_q <= flow_target;
                        end
                        trap_pc_q <= execute_pc_q;
                    end else if (execute_memory_operation) begin
                        effective_address_q <= alu_result;
                        store_data_q <= source_b_q;
                        pending_memory_size_q <= memory_size_q;
                        pending_load_unsigned_q <= load_unsigned_q;
                    end else begin
                        if (flow_taken)
                            pc_q <= flow_target;
                        retire_valid <= 1'b1;
                        retire_pc <= execute_pc_q;
                        retire_instruction <= execute_instruction_q;
                        retire_rd_write <= execute_register_write && (destination_q != 5'd0);
                        retire_rd <= destination_q;
                        retire_rd_data <= execute_writeback_data;
                        retire_mem_access <= 1'b0;
                    end
                end
                STATE_MEMORY: begin
                    if (mem_ready) begin
                        if (mem_error) begin
                            trap_valid <= 1'b1;
                            trap_cause_q <= load_q ? CAUSE_LOAD_ACCESS_FAULT : CAUSE_STORE_ACCESS_FAULT;
                            trap_pc_q <= execute_pc_q;
                            trap_value_q <= effective_address_q;
                        end else if (load_q) begin
                            writeback_data_q <= formatted_load_data;
                        end else begin
                            retire_valid <= 1'b1;
                            retire_pc <= execute_pc_q;
                            retire_instruction <= execute_instruction_q;
                            retire_mem_access <= 1'b1;
                            retire_mem_write <= 1'b1;
                            retire_mem_address <= effective_address_q;
                            retire_mem_strobes <= bus_strobes;
                            retire_mem_data <= bus_formatted_store_data;
                        end
                    end
                end
                STATE_WRITEBACK: begin
                    retire_valid <= 1'b1;
                    retire_pc <= execute_pc_q;
                    retire_instruction <= execute_instruction_q;
                    retire_rd_write <= (destination_q != 5'd0);
                    retire_rd <= destination_q;
                    retire_rd_data <= writeback_data_q;
                    retire_mem_access <= 1'b1;
                    retire_mem_write <= 1'b0;
                    retire_mem_address <= effective_address_q;
                    retire_mem_strobes <= 4'b0000;
                    retire_mem_data <= writeback_data_q;
                end
                default: begin end
            endcase
        end
    end
endmodule
