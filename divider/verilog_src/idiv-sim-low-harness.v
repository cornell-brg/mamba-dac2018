`include "verilog_src/trace.v"

//------------------------------------------------------------------------
// Simulation driver
//------------------------------------------------------------------------
// Currently only 64-bit is supported

module top;

  //----------------------------------------------------------------------
  // Process command line flags
  //----------------------------------------------------------------------

  parameter nbits = 64;
  integer ncycles;
  integer num_inputs;

  initial begin

    if ( !$value$plusargs( "cycle=%d", ncycles ) ) begin
      ncycles = 100;
    end

    if ( $test$plusargs( "help" ) ) begin
      $display( "" );
      $display( " idiv-sim [options]" );
      $display( "" );
      $display( "   +help                 : this message" );
      $display( "   +trace=<int>          : 1 turns on line tracing" );
      $display( "   +cycle=<int>          : number of cycles to simulate" );
      $display( "" );
      $finish;
    end

  end

  //----------------------------------------------------------------------
  // Generate clock
  //----------------------------------------------------------------------

  logic clk = 1;
  always #5 clk = ~clk;

  //----------------------------------------------------------------------
  // Instantiate the harness
  //----------------------------------------------------------------------

  logic reset = 1'b1;

  logic [nbits*2-1:0] inp[100000:0];
  logic [nbits*2-1:0] oup[100000:0];

  task init
  (
    input [15:0] i,
    input [nbits*2-1:0] a,
    input [nbits*2-1:0] b
  );
  begin
    inp[i] = a;
    oup[i] = b;
  end
  endtask

  //----------------------------------------------------------------------
  // Drive the simulation
  //----------------------------------------------------------------------
  logic               req_val;
  logic               req_rdy;
  logic [nbits*2-1:0] req_msg;
  logic               resp_val;
  logic               resp_rdy;
  logic [nbits*2-1:0] resp_msg;

  // I remove the 64 and rely on the default parameter of IntDivRem4 to be
  // compatible with Chisel-generated verilog which is not parameterized.
  IntDivRem4 idiv
  (
    .clk       (clk),
    .reset     (reset),

    .req_msg   (req_msg),
    .req_val   (req_val),
    .req_rdy   (req_rdy),

    .resp_msg  (resp_msg),
    .resp_val  (resp_val),
    .resp_rdy  (resp_rdy)
  );

  logic [nbits*2-1:0] ans;

  integer passed = 0;
  integer cycle;

  initial begin

    #1;

    `include "../divider_input/verilog_input.v"

    // Reset signal

         reset = 1'b1;
    #20; reset = 1'b0;

    // Run the simulation

    cycle = 0;
    req_val = 0;
    resp_rdy = 0;

    while (cycle < ncycles) begin
      resp_rdy = 1;
      if (cycle % 337 == 1) begin
        req_val = 1;
        req_msg = inp[ cycle % num_inputs ];
      end
      else begin
        req_val = 0;
        req_msg = 0;
      end

      if (cycle % 337 == 1)
        if (req_rdy)
          ans = oup[ cycle % num_inputs];

      #10;

      if (resp_val) begin
        if (resp_msg != ans) begin
          $display("Test failed! ans: %x != ref: %x", resp_msg, ans);
          $finish;
        end
        passed += 1;
      end

      cycle += 1;
      idiv.display_trace();

    end

    $write( "[%d passed] idiv", passed );
    $finish;

  end

endmodule

