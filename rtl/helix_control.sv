module helix_control (
    input  logic [2:0] state,
    input  logic       decoupled_configuration,
    input  logic       fetch_accept,
    input  logic       fetch_error,
    input  logic       decode_exception,
    input  logic       execute_exception,
    input  logic       execute_memory_operation,
    input  logic       memory_accept,
    input  logic       memory_error,
    input  logic       memory_is_load,
    output logic [2:0] next_state
);
    localparam logic [2:0] STATE_FETCH    = 3'd0;
    localparam logic [2:0] STATE_DECODE   = 3'd1;
    localparam logic [2:0] STATE_PREPARE  = 3'd2;
    localparam logic [2:0] STATE_EXECUTE  = 3'd3;
    localparam logic [2:0] STATE_MEMORY   = 3'd4;
    localparam logic [2:0] STATE_WRITEBACK = 3'd5;
    localparam logic [2:0] STATE_HALTED   = 3'd6;

    always_comb begin
        next_state = state;
        case (state)
            STATE_FETCH: begin
                if (fetch_accept)
                    next_state = fetch_error ? STATE_HALTED : STATE_DECODE;
            end
            STATE_DECODE: begin
                if (decode_exception)
                    next_state = STATE_HALTED;
                else
                    next_state = decoupled_configuration ? STATE_PREPARE : STATE_EXECUTE;
            end
            STATE_PREPARE: next_state = STATE_EXECUTE;
            STATE_EXECUTE: begin
                if (execute_exception)
                    next_state = STATE_HALTED;
                else
                    next_state = execute_memory_operation ? STATE_MEMORY : STATE_FETCH;
            end
            STATE_MEMORY: begin
                if (memory_accept) begin
                    if (memory_error)
                        next_state = STATE_HALTED;
                    else
                        next_state = memory_is_load ? STATE_WRITEBACK : STATE_FETCH;
                end
            end
            STATE_WRITEBACK: next_state = STATE_FETCH;
            STATE_HALTED: next_state = STATE_HALTED;
            default: next_state = STATE_HALTED;
        endcase
    end
endmodule
