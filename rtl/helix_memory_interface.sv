module helix_memory_interface (
    input  logic [31:0] effective_address,
    input  logic [1:0]  access_size,
    input  logic        load_unsigned,
    input  logic [31:0] store_data,
    input  logic [31:0] bus_read_data,
    output logic        misaligned,
    output logic [31:0] bus_address,
    output logic [3:0]  bus_write_strobes,
    output logic [31:0] bus_write_data,
    output logic [31:0] load_result
);
    logic [31:0] shifted_read_data;
    logic [7:0] selected_byte;
    logic [15:0] selected_half;

    always_comb begin
        bus_address = {effective_address[31:2], 2'b00};
        bus_write_strobes = 4'b0000;
        bus_write_data = store_data << (8 * effective_address[1:0]);
        misaligned = 1'b0;

        case (access_size)
            2'd0: bus_write_strobes = 4'b0001 << effective_address[1:0];
            2'd1: begin
                bus_write_strobes = effective_address[1] ? 4'b1100 : 4'b0011;
                misaligned = effective_address[0];
            end
            2'd2: begin
                bus_write_strobes = 4'b1111;
                misaligned = |effective_address[1:0];
            end
            default: begin
                bus_write_strobes = 4'b0000;
                misaligned = 1'b1;
            end
        endcase

        shifted_read_data = bus_read_data >> (8 * effective_address[1:0]);
        selected_byte = shifted_read_data[7:0];
        selected_half = shifted_read_data[15:0];
        case (access_size)
            2'd0: load_result = load_unsigned ? {24'd0, selected_byte} : {{24{selected_byte[7]}}, selected_byte};
            2'd1: load_result = load_unsigned ? {16'd0, selected_half} : {{16{selected_half[15]}}, selected_half};
            2'd2: load_result = bus_read_data;
            default: load_result = 32'd0;
        endcase
    end
endmodule
