module helix_execution_fabric #(
    parameter integer CONFIGURATION = 0
) (
    input  logic [31:0] operand_a,
    input  logic [31:0] operand_b,
    input  logic [3:0]  operation,
    output logic [31:0] result
);
    localparam bit SHARE_ARITHMETIC = (CONFIGURATION != 0);

    helix_alu #(.SHARE_ARITHMETIC(SHARE_ARITHMETIC)) u_alu (
        .a(operand_a),
        .b(operand_b),
        .op(operation),
        .result(result)
    );
endmodule
