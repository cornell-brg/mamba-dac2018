from pymtl import *
from pclib.rtl import RegEn, Reg, Mux, RShifter, LShifter, Subtractor, ZeroComp
from pclib.valrdy import valrdy_to_str
from pclib.ifcs   import InValRdyIfc, OutValRdyIfc

Q_MUX_SEL_0   = 0
Q_MUX_SEL_LSH = 1

R_MUX_SEL_IN    = 0
R_MUX_SEL_SUB1  = 1
R_MUX_SEL_SUB2  = 2

D_MUX_SEL_IN  = 0
D_MUX_SEL_RSH = 1

class IntDivRem4Dpath( RTLComponent ):

  def __init__( s, nbits ):
    nbitsx2 = nbits * 2

    dtype   = mk_bits(nbits)
    dtypex2 = mk_bits(nbitsx2)

    s.req_msg  = InVPort( dtypex2 )
    s.resp_msg = OutVPort( dtypex2 )

    # Status signals

    s.sub_negative1 = OutVPort( Bits1 )
    s.sub_negative2 = OutVPort( Bits1 )

    # Control signals

    s.quotient_mux_sel  = InVPort( Bits1 )
    s.quotient_reg_en   = InVPort( Bits1 )

    s.remainder_mux_sel = InVPort( Bits2 )
    s.remainder_reg_en  = InVPort( Bits1 )

    s.divisor_mux_sel   = InVPort( Bits1 )

    # Dpath components

    s.remainder_mux = Mux( dtypex2, 3 )( sel = s.remainder_mux_sel )

    @s.update
    def up_remainder_mux_in0():
      s.remainder_mux.in_[R_MUX_SEL_IN] = dtypex2()
      s.remainder_mux.in_[R_MUX_SEL_IN][0:nbits] = s.req_msg[0:nbits]

    s.remainder_reg = RegEn( dtypex2 )(
      in_ = s.remainder_mux.out,
      en  = s.remainder_reg_en,
    )
    # lower bits of resp_msg save the remainder
    s.connect( s.resp_msg[0:nbits], s.remainder_reg.out[0:nbits] )

    s.divisor_mux   = Mux( dtypex2, 2 )( sel = s.divisor_mux_sel )

    @s.update
    def up_divisor_mux_in0():
      s.divisor_mux.in_[D_MUX_SEL_IN] = dtypex2()
      s.divisor_mux.in_[D_MUX_SEL_IN][nbits-1:nbitsx2-1] = s.req_msg[nbits:nbitsx2]

    s.divisor_reg   = Reg( dtypex2 )( in_ = s.divisor_mux.out )

    s.quotient_mux  = Mux( dtype, 2 )( sel = s.quotient_mux_sel )
    s.connect( s.quotient_mux.in_[Q_MUX_SEL_0], 0 )

    s.quotient_reg  = RegEn( dtype )(
      in_ = s.quotient_mux.out,
      en  = s.quotient_reg_en,
      # higher bits of resp_msg save the quotient
      out = s.resp_msg[nbits:nbitsx2],
    )

    # shamt should be 2 bits!
    s.quotient_lsh = LShifter( dtype, 2 )( in_ = s.quotient_reg.out )
    s.connect( s.quotient_lsh.shamt, 2 )

    s.inc = Wire( Bits2 )
    s.connect( s.sub_negative1, s.inc[1] )
    s.connect( s.sub_negative2, s.inc[0] )

    @s.update
    def up_quotient_inc():
      s.quotient_mux.in_[Q_MUX_SEL_LSH] = s.quotient_lsh.out + ~s.inc

    # stage 1/2

    s.sub1 = Subtractor( dtypex2 )(
      in0 = s.remainder_reg.out,
      in1 = s.divisor_reg.out,
      out = s.remainder_mux.in_[R_MUX_SEL_SUB1],
    )
    s.connect( s.sub_negative1, s.sub1.out[nbitsx2-1] )

    s.remainder_mid_mux = Mux( dtypex2, 2 )(
      in_ = { 0: s.sub1.out,
              1: s.remainder_reg.out, },
      sel = s.sub_negative1,
    )

    s.divisor_rsh1 = RShifter( dtypex2, 1 )(
      in_ = s.divisor_reg.out,
    )
    s.connect( s.divisor_rsh1.shamt, 1 )

    # stage 2/2

    s.sub2 = Subtractor( dtypex2 )(
      in0 = s.remainder_mid_mux.out,
      in1 = s.divisor_rsh1.out,
      out = s.remainder_mux.in_[R_MUX_SEL_SUB2],
    )

    s.connect( s.sub_negative2, s.sub2.out[nbitsx2-1] )

    s.divisor_rsh2 = RShifter( dtypex2, 1 )(
      in_ = s.divisor_rsh1.out,
      out = s.divisor_mux.in_[D_MUX_SEL_RSH],
    )
    s.connect( s.divisor_rsh2.shamt, 1 )

class IntDivRem4Ctrl( RTLComponent ):

  def __init__( s, nbits ):
    s.req_val  = InVPort( Bits1 )
    s.req_rdy  = OutVPort( Bits1 )
    s.resp_val = OutVPort( Bits1 )
    s.resp_rdy = InVPort( Bits1 )

    # Status signals

    s.sub_negative1 = InVPort( Bits1 )
    s.sub_negative2 = InVPort( Bits1 )

    # Control signals

    s.quotient_mux_sel  = OutVPort( Bits1 )
    s.quotient_reg_en   = OutVPort( Bits1 )

    s.remainder_mux_sel = OutVPort( Bits2 )
    s.remainder_reg_en  = OutVPort( Bits1 )

    s.divisor_mux_sel   = OutVPort( Bits1 )

    state_dtype = mk_bits( 1+clog2(nbits) )
    s.state = Reg( state_dtype )

    s.STATE_IDLE = state_dtype(0)
    s.STATE_DONE = state_dtype(1)
    s.STATE_CALC = state_dtype(1+nbits/2)

    @s.update
    def state_transitions():

      curr_state = s.state.out

      if   curr_state == s.STATE_IDLE:
        if s.req_val and s.req_rdy:
          s.state.in_ = s.STATE_CALC

      elif curr_state == s.STATE_DONE:
        if s.resp_val and s.resp_rdy:
          s.state.in_ = s.STATE_IDLE

      else:
        s.state.in_ = curr_state - 1

    @s.update
    def state_outputs():

      curr_state = s.state.out

      if   curr_state == s.STATE_IDLE:
        s.req_rdy     = Bits1( 1 )
        s.resp_val    = Bits1( 0 )

        s.remainder_mux_sel = Bits2( R_MUX_SEL_IN )
        s.remainder_reg_en  = Bits1( 1 )

        s.quotient_mux_sel  = Bits2( Q_MUX_SEL_0 )
        s.quotient_reg_en   = Bits1( 1 )

        s.divisor_mux_sel   = Bits1( D_MUX_SEL_IN )

      elif curr_state == s.STATE_DONE:
        s.req_rdy     = Bits1( 0 )
        s.resp_val    = Bits1( 1 )

        s.quotient_mux_sel  = Bits2( Q_MUX_SEL_0 )
        s.quotient_reg_en   = Bits1( 0 )

        s.remainder_mux_sel = Bits2( R_MUX_SEL_IN )
        s.remainder_reg_en  = Bits1( 0 )

        s.divisor_mux_sel   = Bits1( D_MUX_SEL_IN )

      else: # calculating
        s.req_rdy     = Bits1( 0 )
        s.resp_val    = Bits1( 0 )

        s.remainder_reg_en = ~(s.sub_negative1 & s.sub_negative2)
        if s.sub_negative2:
          s.remainder_mux_sel = Bits2( R_MUX_SEL_SUB1 )
        else:
          s.remainder_mux_sel = Bits2( R_MUX_SEL_SUB2 )

        s.quotient_reg_en   = Bits1( 1 )
        s.quotient_mux_sel  = Bits1( Q_MUX_SEL_LSH )

        s.divisor_mux_sel   = Bits1( D_MUX_SEL_RSH )

class IntDivRem4( RTLComponent ):

  def __init__( s, nbits=32 ):
    assert nbits % 2 == 0

    s.req  = InValRdyIfc( mk_bits(nbits*2) )
    s.resp = OutValRdyIfc( mk_bits(nbits*2) )

    s.dpath = IntDivRem4Dpath( nbits ) (
      req_msg  = s.req.msg,
      resp_msg = s.resp.msg,
    )

    s.ctrl = IntDivRem4Ctrl( nbits ) (
      req_val   = s.req.val,
      req_rdy   = s.req.rdy,
      resp_val  = s.resp.val,
      resp_rdy  = s.resp.rdy,

      # Status signals

      sub_negative1 = s.dpath.sub_negative1,
      sub_negative2 = s.dpath.sub_negative2,

      # Control signals

      quotient_mux_sel  = s.dpath.quotient_mux_sel,
      quotient_reg_en   = s.dpath.quotient_reg_en,

      remainder_mux_sel = s.dpath.remainder_mux_sel,
      remainder_reg_en  = s.dpath.remainder_reg_en,

      divisor_mux_sel   = s.dpath.divisor_mux_sel,
    )

  def line_trace( s ):
    return "Rem:{} Quo:{} Div:{}".format( s.dpath.remainder_reg.out,
                                          s.dpath.quotient_reg.out,
                                          s.dpath.divisor_reg.out )
