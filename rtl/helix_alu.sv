module helix_alu #(
    parameter bit SHARE_ARITHMETIC = 1'b0
) (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [3:0]  op,
    output logic [31:0] result
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

    logic [31:0] arithmetic_result;

    always_comb begin
        if (SHARE_ARITHMETIC) begin
            if (op == ALU_SUB)
                arithmetic_result = a + (~b) + 32'd1;
            else
                arithmetic_result = a + b;
        end else begin
            case (op)
                ALU_SUB: arithmetic_result = a - b;
                default: arithmetic_result = a + b;
            endcase
        end

        case (op)
            ALU_ADD, ALU_SUB: result = arithmetic_result;
            ALU_SLL:          result = a << b[4:0];
            ALU_SLT:          result = {31'd0, ($signed(a) < $signed(b))};
            ALU_SLTU:         result = {31'd0, (a < b)};
            ALU_XOR:          result = a ^ b;
            ALU_SRL:          result = a >> b[4:0];
            ALU_SRA:          result = $signed(a) >>> b[4:0];
            ALU_OR:           result = a | b;
            ALU_AND:          result = a & b;
            ALU_COPY_B:       result = b;
            default:          result = 32'd0;
        endcase
    end
endmodule
