module helix_immediate (
    input  logic [31:0] instruction,
    input  logic [2:0]  immediate_kind,
    output logic [31:0] immediate
);
    localparam logic [2:0] IMM_I     = 3'd0;
    localparam logic [2:0] IMM_S     = 3'd1;
    localparam logic [2:0] IMM_B     = 3'd2;
    localparam logic [2:0] IMM_U     = 3'd3;
    localparam logic [2:0] IMM_J     = 3'd4;
    localparam logic [2:0] IMM_SHIFT = 3'd5;

    always_comb begin
        case (immediate_kind)
            IMM_I:     immediate = {{20{instruction[31]}}, instruction[31:20]};
            IMM_S:     immediate = {{20{instruction[31]}}, instruction[31:25], instruction[11:7]};
            IMM_B:     immediate = {{19{instruction[31]}}, instruction[31], instruction[7], instruction[30:25], instruction[11:8], 1'b0};
            IMM_U:     immediate = {instruction[31:12], 12'b0};
            IMM_J:     immediate = {{11{instruction[31]}}, instruction[31], instruction[19:12], instruction[20], instruction[30:21], 1'b0};
            IMM_SHIFT: immediate = {27'd0, instruction[24:20]};
            default:   immediate = 32'd0;
        endcase
    end
endmodule
