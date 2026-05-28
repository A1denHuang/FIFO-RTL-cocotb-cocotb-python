`timescale 1ns/1ps

module sync_fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 16,
    parameter ALMOST_FULL_THRESHOLD = DEPTH - 2
) (
    input wire clk,
    input wire rst_n,

    input wire wr_en,
    input wire rd_en,
    input wire [DATA_WIDTH-1:0] din,

    output reg [DATA_WIDTH-1:0] dout,
    output wire empty,
    output wire full,
    output wire almost_full
);

    function integer clog2;
        input integer value;
        integer i;
        begin
            clog2 = 0;
            for (i = value - 1; i > 0; i = i >> 1)
                clog2 = clog2 + 1;
        end
    endfunction

    localparam ADDR_WIDTH = clog2(DEPTH);
    localparam COUNT_WIDTH = clog2(DEPTH + 1);

    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    reg [ADDR_WIDTH-1:0] wr_ptr;
    reg [ADDR_WIDTH-1:0] rd_ptr;
    reg [COUNT_WIDTH-1:0] count;

    wire write_ok;
    wire read_ok;

    assign empty = (count == 0);
    assign full = (count == DEPTH);
    assign almost_full = (count >= ALMOST_FULL_THRESHOLD);

    assign write_ok = wr_en && (!full || read_ok);
    assign read_ok = rd_en && !empty;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= {ADDR_WIDTH{1'b0}};
            rd_ptr <= {ADDR_WIDTH{1'b0}};
            count <= {COUNT_WIDTH{1'b0}};
            dout <= {DATA_WIDTH{1'b0}};
        end else begin
            if (write_ok) begin
                mem[wr_ptr] <= din;
                if (wr_ptr == DEPTH - 1)
                    wr_ptr <= {ADDR_WIDTH{1'b0}};
                else
                    wr_ptr <= wr_ptr + 1'b1;
            end

            if (read_ok) begin
                dout <= mem[rd_ptr];
                if (rd_ptr == DEPTH - 1)
                    rd_ptr <= {ADDR_WIDTH{1'b0}};
                else
                    rd_ptr <= rd_ptr + 1'b1;
            end

            case ({write_ok, read_ok})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: count <= count;
            endcase
        end
    end

endmodule
