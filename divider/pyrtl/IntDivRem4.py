import random
random.seed(0xdeadbeef)

import pytest
import sys
import os

from pyrtl import *

def Subtractor( in0, in1 ):
  assert len(in0) == len(in1)
  out = WireVector( len(in0) )
  out <<= in0 - in1
  return out

def LeftLogicalShifter( in0, shamt ):
  out = WireVector( len(in0) )
  # Damn it doesn't support shifting!
  # out <<= in0 << shamt
  # concat is
  out <<= concat( in0[:-shamt], Const( 0, bitwidth=shamt ) )
  return out

def RightLogicalShifter( in0, shamt ):
  out = WireVector( len(in0) )
  # Damn it doesn't support shifting!
  # out <<= in0 >> shamt
  out <<= concat( Const(0, bitwidth=shamt), in0[shamt:] )

  return out

def RegEn( in_, en ):
  out = Register( len(in_) )
  with conditional_assignment:
    with en:
      out.next |= in_
  return out

def RegRst( in_, rst, reset_value=0 ):
  out = Register( len(in_) )
  with conditional_assignment:
    with rst:
      out.next |= Const(reset_value)
    with otherwise:
      out.next |= in_
  return out

Q_MUX_SEL_0   = 0
Q_MUX_SEL_LSH = 1

R_MUX_SEL_IN    = 0
R_MUX_SEL_SUB1  = 1
R_MUX_SEL_SUB2  = 2

D_MUX_SEL_IN  = 0
D_MUX_SEL_RSH = 1

class IntDivRem4Ctrl(object):

  def __init__( s, nbits ):

    s.reset = WireVector( 1 )
    s.req_val = WireVector( 1 )
    s.req_rdy = WireVector( 1 )
    s.resp_val = WireVector( 1 )
    s.resp_rdy = WireVector( 1 )
    s.sub_negative1 = WireVector( 1 )
    s.sub_negative2 = WireVector( 1 )
    s.quotient_mux_sel = WireVector( 1 )
    s.quotient_reg_en = WireVector( 1 )
    s.remainder_mux_sel = WireVector( 2 )
    s.remainder_reg_en = WireVector( 1 )
    s.divisor_mux_sel = WireVector( 1 )

    import math
    state_nbits = 1+int( math.ceil( math.log( nbits, 2 ) ) )

    state_in_ = WireVector( state_nbits )
    state_out = RegRst( state_in_, s.reset, 0 )

    STATE_IDLE = Const(0)
    STATE_DONE = Const(1)
    STATE_CALC = Const(1+nbits/2)

    with conditional_assignment:

      with state_out == STATE_IDLE:
        with s.req_val & s.req_rdy:
          state_in_ |= STATE_CALC

      with state_out == STATE_DONE:
        with s.resp_val & s.resp_rdy:
          state_in_ |= STATE_IDLE

      with otherwise:
        state_in_ |= state_out - 1

    with conditional_assignment:

      with state_out == STATE_IDLE:
        s.req_rdy  |= 1
        s.resp_val |= 0

        s.remainder_mux_sel |= R_MUX_SEL_IN
        s.remainder_reg_en  |= 1

        s.quotient_mux_sel |= Q_MUX_SEL_0
        s.quotient_reg_en  |= 1

        s.divisor_mux_sel  |= D_MUX_SEL_IN

      with state_out == STATE_DONE:
        s.req_rdy  |= 0
        s.resp_val |= 1

        s.quotient_mux_sel |= Q_MUX_SEL_0
        s.quotient_reg_en  |= 0

        s.remainder_mux_sel |= R_MUX_SEL_IN
        s.remainder_reg_en  |= 0

        s.divisor_mux_sel   |= D_MUX_SEL_IN

      with otherwise: # calculating
        s.req_rdy     |= 0
        s.resp_val    |= 0

        s.remainder_reg_en |= ~(s.sub_negative1 & s.sub_negative2)
        with s.sub_negative2:
          s.remainder_mux_sel |= R_MUX_SEL_SUB1
        with otherwise:
          s.remainder_mux_sel |= R_MUX_SEL_SUB2

        s.quotient_reg_en   |= 1
        s.quotient_mux_sel  |= Q_MUX_SEL_LSH

        s.divisor_mux_sel   |= D_MUX_SEL_RSH

class IntDivRem4Dpath(object):

  def __init__( s, nbits ):
    s.req_msg = WireVector( nbits*2 )
    s.resp_msg = WireVector( nbits*2 )

    s.sub_negative1 = WireVector( 1 )
    s.sub_negative2 = WireVector( 1 )
    s.quotient_mux_sel = WireVector( 1 )
    s.quotient_reg_en = WireVector( 1 )
    s.remainder_mux_sel = WireVector( 2 )
    s.remainder_reg_en = WireVector( 1 )
    s.divisor_mux_sel = WireVector( 1 )

    sub1_out          = WireVector( nbits*2 )
    sub2_out          = WireVector( nbits*2 )
    divisor_rsh2_out  = WireVector( nbits*2 )
    quotient_lsh_out  = WireVector( nbits )

    remainder_mux_in_in = WireVector( nbits*2 )

    remainder_mux_in_in <<= concat( Const(0, bitwidth=nbits), s.req_msg[0:nbits] )

    remainder_mux = mux( s.remainder_mux_sel,
                         remainder_mux_in_in, # R_MUX_SEL_IN    = 0
                         sub1_out, # R_MUX_SEL_SUB1  = 1
                         sub2_out, # R_MUX_SEL_SUB2  = 2
                         default=0)

    remainder_reg = RegEn( remainder_mux,
                           s.remainder_reg_en )

    divisor_mux_in_in = WireVector( nbits*2 )
    divisor_mux_in_in <<= concat( Const(0, bitwidth=1),
                                  s.req_msg[nbits:nbits*2],
                                  Const(0, bitwidth=nbits-1) )

    divisor_mux = mux( s.divisor_mux_sel,
                       divisor_mux_in_in, # D_MUX_SEL_IN = 0
                       divisor_rsh2_out, # D_MUX_SEL_RSH = 1
                     )

    divisor_reg = Register( bitwidth = nbits*2 )
    divisor_reg.next <<= divisor_mux

    quotient_mux_in_lsh = WireVector( nbits )
    quotient_mux_in_lsh <<= quotient_lsh_out + concat( ~s.sub_negative1, ~s.sub_negative2 )

    quotient_mux = mux( s.quotient_mux_sel,
                        0, # Q_MUX_SEL_0 = 0
                        quotient_mux_in_lsh, # Q_MUX_SEL_LSH = 1
                      )

    quotient_reg = RegEn( quotient_mux, s.quotient_reg_en )
    quotient_lsh = LeftLogicalShifter( quotient_reg, 2 )
    quotient_lsh_out <<= quotient_lsh

    sub1 = Subtractor( remainder_reg, divisor_reg )
    sub1_out <<= sub1
    s.sub_negative1 <<= sub1[nbits*2-1]

    divisor_rsh1 = RightLogicalShifter( divisor_reg, 1 )

    remainder_mid_mux = mux( s.sub_negative1,
                             sub1_out, remainder_reg )

    sub2 = Subtractor( remainder_mid_mux, divisor_rsh1 )
    sub2_out <<= sub2
    s.sub_negative2 <<= sub2_out[nbits*2-1]

    divisor_rsh2 = RightLogicalShifter( divisor_rsh1, 1 )
    divisor_rsh2_out <<= divisor_rsh2

    s.resp_msg <<= concat( quotient_reg, remainder_reg[0:nbits] )

class IntDivRem4(object):

  def __init__( s, nbits ):
    s.reset = Input( 1, 'reset' )

    s.req_val = Input( 1, 'req_val' )
    s.req_rdy = Output( 1, 'req_rdy' )
    s.req_msg = Input( nbits*2, 'req_msg' )

    s.resp_val = Output( 1, 'resp_val' )
    s.resp_rdy = Input( 1, 'resp_rdy' )
    s.resp_msg = Output( nbits*2, 'resp_msg' )

    # Don't need to write s.ctrl unless you want to access from outside
    ctrl  = IntDivRem4Ctrl( nbits )
    dpath = IntDivRem4Dpath( nbits )

    ctrl.reset <<= s.reset
    ctrl.req_val  <<= s.req_val
    ctrl.resp_rdy <<= s.resp_rdy
    s.req_rdy  <<= ctrl.req_rdy
    s.resp_val <<= ctrl.resp_val

    dpath.req_msg <<= s.req_msg
    s.resp_msg <<= dpath.resp_msg

    ctrl.sub_negative1 <<= dpath.sub_negative1
    ctrl.sub_negative2 <<= dpath.sub_negative2

    dpath.quotient_mux_sel <<= ctrl.quotient_mux_sel
    dpath.quotient_reg_en <<= ctrl.quotient_reg_en
    dpath.remainder_mux_sel <<= ctrl.remainder_mux_sel
    dpath.remainder_reg_en <<= ctrl.remainder_reg_en
    dpath.divisor_mux_sel <<= ctrl.divisor_mux_sel
