# This is the PyMTL wrapper for the corresponding Verilog RTL model.

from pymtl        import *
from pclib.ifcs   import InValRdyBundle, OutValRdyBundle

class IntDivRem4( VerilogModel ):

  # Verilog module setup

  vlinetrace = True

  # Constructor

  def __init__( s, nbits=64 ):

    # Interface

    s.req   = InValRdyBundle  ( nbits*2 )
    s.resp  = OutValRdyBundle ( nbits*2 )

    # Verilog ports
    s.set_params({
      'nbits': nbits,
    })

    s.set_ports({
      'clk'         : s.clk,
      'reset'       : s.reset,

      'req_val'     : s.req.val,
      'req_rdy'     : s.req.rdy,
      'req_msg'     : s.req.msg,

      'resp_val'    : s.resp.val,
      'resp_rdy'    : s.resp.rdy,
      'resp_msg'    : s.resp.msg,
    })
