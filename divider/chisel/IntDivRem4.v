`include "chisel/IntDivRem4_raw.v"
`include "verilog_src/trace.v"
module IntDivRem4(
  input          clk,
  input          reset,
  output         req_rdy,
  input          req_val,
  input  [127:0] req_msg,
  input          resp_rdy,
  output         resp_val,
  output [127:0] resp_msg
);
  IntDivRem4_raw idiv (
    .clock(clk),
    .reset(reset),
    .io_req_ready(req_rdy),
    .io_req_valid(req_val),
    .io_req_bits(req_msg),
    .io_resp_ready(resp_rdy),
    .io_resp_valid(resp_val),
    .io_resp_bits(resp_msg)
  );

  `ifndef SYNTHESIS

  logic [`VC_TRACE_NBITS-1:0] str;
  `VC_TRACE_BEGIN
  begin
    vc_trace.append_str( trace_str, "(" );

    $sformat( str, "Rem:%x", idiv.dpath.remainder_reg_io_out );
    vc_trace.append_str( trace_str, str );
    vc_trace.append_str( trace_str, " " );

    $sformat( str, "Quo:%x", idiv.dpath.quotient_reg_io_out );
    vc_trace.append_str( trace_str, str );
    vc_trace.append_str( trace_str, " " );

    $sformat( str, "Div:%x", idiv.dpath.divisor_reg_out );
    vc_trace.append_str( trace_str, str );
    vc_trace.append_str( trace_str, " " );

    vc_trace.append_str( trace_str, ")" );

  end
  `VC_TRACE_END

  `endif /* SYNTHESIS */

endmodule
