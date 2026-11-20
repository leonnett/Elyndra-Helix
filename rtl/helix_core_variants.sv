module helix_core_a (
    input logic clk, input logic reset_n,
    output logic mem_valid, output logic mem_write, output logic [31:0] mem_address,
    output logic [31:0] mem_write_data, output logic [3:0] mem_write_strobes,
    input logic [31:0] mem_read_data, input logic mem_ready, input logic mem_error,
    output logic retire_valid, output logic [31:0] retire_pc, output logic [31:0] retire_instruction,
    output logic retire_rd_write, output logic [4:0] retire_rd, output logic [31:0] retire_rd_data,
    output logic retire_mem_access, output logic retire_mem_write, output logic [31:0] retire_mem_address,
    output logic [3:0] retire_mem_strobes, output logic [31:0] retire_mem_data,
    output logic trap_valid, output logic [31:0] trap_cause, output logic [31:0] trap_pc,
    output logic [31:0] trap_value, output logic [2:0] debug_state
);
    helix_core #(.EXEC_CONFIG(0)) u_core (
        .clk(clk), .reset_n(reset_n), .mem_valid(mem_valid), .mem_write(mem_write),
        .mem_address(mem_address), .mem_write_data(mem_write_data), .mem_write_strobes(mem_write_strobes),
        .mem_read_data(mem_read_data), .mem_ready(mem_ready), .mem_error(mem_error),
        .retire_valid(retire_valid), .retire_pc(retire_pc), .retire_instruction(retire_instruction),
        .retire_rd_write(retire_rd_write), .retire_rd(retire_rd), .retire_rd_data(retire_rd_data),
        .retire_mem_access(retire_mem_access), .retire_mem_write(retire_mem_write),
        .retire_mem_address(retire_mem_address), .retire_mem_strobes(retire_mem_strobes),
        .retire_mem_data(retire_mem_data), .trap_valid(trap_valid), .trap_cause(trap_cause),
        .trap_pc(trap_pc), .trap_value(trap_value), .debug_state(debug_state)
    );
endmodule

module helix_core_b (
    input logic clk, input logic reset_n,
    output logic mem_valid, output logic mem_write, output logic [31:0] mem_address,
    output logic [31:0] mem_write_data, output logic [3:0] mem_write_strobes,
    input logic [31:0] mem_read_data, input logic mem_ready, input logic mem_error,
    output logic retire_valid, output logic [31:0] retire_pc, output logic [31:0] retire_instruction,
    output logic retire_rd_write, output logic [4:0] retire_rd, output logic [31:0] retire_rd_data,
    output logic retire_mem_access, output logic retire_mem_write, output logic [31:0] retire_mem_address,
    output logic [3:0] retire_mem_strobes, output logic [31:0] retire_mem_data,
    output logic trap_valid, output logic [31:0] trap_cause, output logic [31:0] trap_pc,
    output logic [31:0] trap_value, output logic [2:0] debug_state
);
    helix_core #(.EXEC_CONFIG(1)) u_core (
        .clk(clk), .reset_n(reset_n), .mem_valid(mem_valid), .mem_write(mem_write),
        .mem_address(mem_address), .mem_write_data(mem_write_data), .mem_write_strobes(mem_write_strobes),
        .mem_read_data(mem_read_data), .mem_ready(mem_ready), .mem_error(mem_error),
        .retire_valid(retire_valid), .retire_pc(retire_pc), .retire_instruction(retire_instruction),
        .retire_rd_write(retire_rd_write), .retire_rd(retire_rd), .retire_rd_data(retire_rd_data),
        .retire_mem_access(retire_mem_access), .retire_mem_write(retire_mem_write),
        .retire_mem_address(retire_mem_address), .retire_mem_strobes(retire_mem_strobes),
        .retire_mem_data(retire_mem_data), .trap_valid(trap_valid), .trap_cause(trap_cause),
        .trap_pc(trap_pc), .trap_value(trap_value), .debug_state(debug_state)
    );
endmodule

module helix_core_c (
    input logic clk, input logic reset_n,
    output logic mem_valid, output logic mem_write, output logic [31:0] mem_address,
    output logic [31:0] mem_write_data, output logic [3:0] mem_write_strobes,
    input logic [31:0] mem_read_data, input logic mem_ready, input logic mem_error,
    output logic retire_valid, output logic [31:0] retire_pc, output logic [31:0] retire_instruction,
    output logic retire_rd_write, output logic [4:0] retire_rd, output logic [31:0] retire_rd_data,
    output logic retire_mem_access, output logic retire_mem_write, output logic [31:0] retire_mem_address,
    output logic [3:0] retire_mem_strobes, output logic [31:0] retire_mem_data,
    output logic trap_valid, output logic [31:0] trap_cause, output logic [31:0] trap_pc,
    output logic [31:0] trap_value, output logic [2:0] debug_state
);
    helix_core #(.EXEC_CONFIG(2)) u_core (
        .clk(clk), .reset_n(reset_n), .mem_valid(mem_valid), .mem_write(mem_write),
        .mem_address(mem_address), .mem_write_data(mem_write_data), .mem_write_strobes(mem_write_strobes),
        .mem_read_data(mem_read_data), .mem_ready(mem_ready), .mem_error(mem_error),
        .retire_valid(retire_valid), .retire_pc(retire_pc), .retire_instruction(retire_instruction),
        .retire_rd_write(retire_rd_write), .retire_rd(retire_rd), .retire_rd_data(retire_rd_data),
        .retire_mem_access(retire_mem_access), .retire_mem_write(retire_mem_write),
        .retire_mem_address(retire_mem_address), .retire_mem_strobes(retire_mem_strobes),
        .retire_mem_data(retire_mem_data), .trap_valid(trap_valid), .trap_cause(trap_cause),
        .trap_pc(trap_pc), .trap_value(trap_value), .debug_state(debug_state)
    );
endmodule
