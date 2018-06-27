package idiv

import chisel3._
import chisel3.util._

class Subtractor(nbits: Int) extends Module {
  val io = IO(new Bundle {
    val in0 = Input( UInt(nbits.W) )
    val in1 = Input( UInt(nbits.W) )
    val out = Output( UInt(nbits.W) )
  })

  io.out := io.in0 - io.in1
}

class LeftLogicalShifter(nbits: Int, shamt_nbits: Int) extends Module {
  val io = IO(new Bundle {
    val in_ = Input( UInt(nbits.W) )
    val shamt = Input( UInt(shamt_nbits.W) )
    val out = Output( UInt(nbits.W) )
  })

  io.out := io.in_ << io.shamt
}

class RightLogicalShifter(nbits: Int, shamt_nbits: Int) extends Module {
  val io = IO(new Bundle {
    val in_ = Input( UInt(nbits.W) )
    val shamt = Input( UInt(shamt_nbits.W) )
    val out = Output( UInt(nbits.W) )
  })

  io.out := io.in_ >> io.shamt
}

class RegEn(nbits: Int) extends Module {
  val io = IO(new Bundle {
    val in_ = Input( UInt(nbits.W) )
    val en  = Input( Bool() )
    val out = Output( UInt(nbits.W) )
  })

  val v = Reg(UInt(nbits.W))

  when (io.en)  { v := io.in_ }

  io.out := v
}

class CS extends Bundle {
  val sub_negative1 = Input( Bool() )
  val sub_negative2 = Input( Bool() )
  val divisor_mux_sel = Output( Bool() )
  val quotient_mux_sel = Output( Bool() )
  val quotient_reg_en = Output( Bool() )
  val remainder_mux_sel= Output( UInt(2.W) )
  val remainder_reg_en = Output( Bool() )
}

class CtrlIO extends Bundle {
  val req_val  = Input( Bool() )
  val resp_rdy = Input( Bool() )
  val req_rdy  = Output( Bool() )
  val resp_val = Output( Bool() )
  val cs = new CS
}

class DpathIO(nbits: Int) extends Bundle {
  val req_msg = Input( UInt((nbits*2).W) )
  val resp_msg = Output( UInt((nbits*2).W) )
  val cs = Flipped(new CS)
}

class IntDivRem4Ctrl(nbits: Int) extends Module {

  val io = IO(new CtrlIO)

  val D_MUX_SEL_IN = 0.asUInt(2.W)
  val D_MUX_SEL_RSH = 1.asUInt(2.W)
  val Q_MUX_SEL_0 = 0.asUInt(2.W)
  val Q_MUX_SEL_LSH = 1.asUInt(2.W)
  val R_MUX_SEL_IN = 0.asUInt(2.W)
  val R_MUX_SEL_SUB1 = 1.asUInt(2.W)
  val R_MUX_SEL_SUB2 = 2.asUInt(2.W)

  val state_nbits = 1+log2Up(nbits)
  val STATE_CALC = (1+nbits/2).asUInt(state_nbits.W)
  val STATE_DONE = 1.asUInt(state_nbits.W)
  val STATE_IDLE = 0.asUInt(state_nbits.W)

  val state = Reg(init=STATE_IDLE)

  // state transition
  when (state === STATE_IDLE)
  {
    when (io.req_val & io.req_rdy)
    {
      state := STATE_CALC
    }
  }
  .elsewhen (state === STATE_DONE)
  {
    when (io.resp_val & io.resp_rdy)
    {
      state := STATE_IDLE
    }
  }.otherwise
  {
    state := state - 1.U
  }

  // state output
  when (state === STATE_IDLE)
  {
    io.req_rdy := true.B
    io.resp_val := false.B
    io.cs.remainder_mux_sel := R_MUX_SEL_IN
    io.cs.remainder_reg_en := 1.asUInt(1.W)
    io.cs.quotient_mux_sel := Q_MUX_SEL_0
    io.cs.quotient_reg_en := 1.asUInt(1.W)
    io.cs.divisor_mux_sel := D_MUX_SEL_IN
  }
  .elsewhen (state === STATE_DONE)
  {
    io.req_rdy := false.B
    io.resp_val := true.B
    io.cs.quotient_mux_sel := Q_MUX_SEL_0
    io.cs.quotient_reg_en := 0.asUInt(1.W)
    io.cs.remainder_mux_sel := R_MUX_SEL_IN
    io.cs.remainder_reg_en := 0.asUInt(1.W)
    io.cs.divisor_mux_sel := D_MUX_SEL_IN
  }
  .otherwise
  {
    io.req_rdy := false.B
    io.resp_val := false.B
    io.cs.remainder_reg_en := ~(io.cs.sub_negative1 & io.cs.sub_negative2);
    when (io.cs.sub_negative2)
    {
      io.cs.remainder_mux_sel := R_MUX_SEL_SUB1
    }
    .otherwise
    {
      io.cs.remainder_mux_sel := R_MUX_SEL_SUB2
    }
    io.cs.quotient_reg_en := 1.asUInt(1.W)
    io.cs.quotient_mux_sel := Q_MUX_SEL_LSH
    io.cs.divisor_mux_sel := D_MUX_SEL_RSH
  }
}

class IntDivRem4Dpath(nbits: Int) extends Module {
  val io = IO(new DpathIO(nbits))

  val D_MUX_SEL_IN = 0.asUInt(2.W)
  val D_MUX_SEL_RSH = 1.asUInt(2.W)
  val Q_MUX_SEL_0 = 0.asUInt(2.W)
  val Q_MUX_SEL_LSH = 1.asUInt(2.W)
  val R_MUX_SEL_IN = 0.asUInt(2.W)
  val R_MUX_SEL_SUB1 = 1.asUInt(2.W)
  val R_MUX_SEL_SUB2 = 2.asUInt(2.W)

  val sub1_out = Wire( UInt((nbits*2).W) )
  val sub2_out = Wire( UInt((nbits*2).W) )

  val remainder_mux_out = MuxLookup( io.cs.remainder_mux_sel, UInt(0), Seq(
    R_MUX_SEL_IN   -> Cat( Fill(nbits, 0.U), io.req_msg(nbits-1,0) ),
    R_MUX_SEL_SUB1 -> sub1_out,
    R_MUX_SEL_SUB2 -> sub2_out
  ))

  val remainder_reg = Module(new RegEn(nbits*2))

  remainder_reg.io.in_ := remainder_mux_out
  remainder_reg.io.en  := io.cs.remainder_reg_en

  val divisor_mux_in_in = Cat( Fill(1,0.U),
                                io.req_msg(nbits*2-1,nbits),
                                Fill(nbits-1,0.U))

  val divisor_rsh2_out = Wire( UInt((nbits*2).W) )
  // !!! If sel then out else in
  val divisor_mux_out = Mux( io.cs.divisor_mux_sel, divisor_rsh2_out, divisor_mux_in_in )

  val divisor_reg_out = Reg( UInt((nbits*2).W) )
  divisor_reg_out := divisor_mux_out

  val quotient_reg = Module( new RegEn(nbits) )

  quotient_reg.io.en := io.cs.quotient_reg_en

  val quotient_lsh = Module( new LeftLogicalShifter(nbits*2, 2) )
  quotient_lsh.io.in_   := quotient_reg.io.out
  quotient_lsh.io.shamt := 2.asUInt(2.W)

  // !!! If sel then out else in
  val quotient_mux_out = Mux( io.cs.quotient_mux_sel,
                          quotient_lsh.io.out + Cat( ~io.cs.sub_negative1, ~io.cs.sub_negative2 ),
                          0.U )

  quotient_reg.io.in_ := quotient_mux_out

  val sub1 = Module( new Subtractor(nbits*2) )

  sub1.io.in0 := remainder_reg.io.out
  sub1.io.in1 := divisor_reg_out
  sub1_out    := sub1.io.out

  io.cs.sub_negative1 := sub1.io.out(nbits*2-1)

  val divisor_rsh1 = Module( new RightLogicalShifter(nbits*2, 1) )

  divisor_rsh1.io.in_   := divisor_reg_out
  divisor_rsh1.io.shamt := 1.asUInt(1.W)

  // !!! If sel then out else in
  val remainder_mid_mux_out = Mux(  io.cs.sub_negative1,
                                    remainder_reg.io.out,
                                    sub1.io.out )

  val sub2 = Module( new Subtractor(nbits*2) )
  sub2.io.in0 := remainder_mid_mux_out
  sub2.io.in1 := divisor_rsh1.io.out
  sub2_out    := sub2.io.out

  io.cs.sub_negative2 := sub2.io.out(nbits*2-1)

  val divisor_rsh2 = Module( new RightLogicalShifter(nbits*2, 1) )
  divisor_rsh2.io.in_   := divisor_rsh1.io.out
  divisor_rsh2.io.shamt := 1.asUInt(1.W)
  divisor_rsh2_out      := divisor_rsh2.io.out

  io.resp_msg := Cat( quotient_reg.io.out, remainder_reg.io.out(nbits-1,0) )
}

class IntDivRem4_raw(nbits: Int) extends Module {
  val io = IO(new Bundle {
    val req  = Flipped( Decoupled( UInt((nbits*2).W) ) )
    val resp = Decoupled(UInt((nbits*2).W))
  })

  val ctrl  = Module( new IntDivRem4Ctrl(nbits) )
  val dpath = Module( new IntDivRem4Dpath(nbits) )
  
  ctrl.io.cs <> dpath.io.cs
  ctrl.io.req_val  := io.req.valid
  io.req.ready     := ctrl.io.req_rdy
  ctrl.io.resp_rdy := io.resp.ready
  io.resp.valid    := ctrl.io.resp_val
  dpath.io.req_msg := io.req.bits
  io.resp.bits     := dpath.io.resp_msg
}

object MyDriver extends App {
  chisel3.Driver.execute(args, () => new IntDivRem4_raw(64))
}
