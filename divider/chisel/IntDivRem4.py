# This is the PyMTL wrapper for the corresponding Verilog RTL model.
import os
from pymtl        import *
from pclib.ifcs   import InValRdyBundle, OutValRdyBundle

class IntDivRem4( VerilogModel ):

  # Verilog module setup

  modulename = 'IntDivRem4_raw'
  # Constructor

  def __init__( s ):

    # Interface

    s.req   = InValRdyBundle  ( 128 )
    s.resp  = OutValRdyBundle ( 128 )

    s.set_ports({
      'clock'         : s.clk,
      'reset'         : s.reset,

      'io_req_valid'     : s.req.val,
      'io_req_ready'     : s.req.rdy,
      'io_req_bits'      : s.req.msg,

      'io_resp_valid'    : s.resp.val,
      'io_resp_ready'    : s.resp.rdy,
      'io_resp_bits'     : s.resp.msg,
    })
