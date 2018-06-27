import random
random.seed(0xdeadbeef)

def valrdy_to_str( msg, val, rdy ):

  str_   = "{}".format( msg )
  nchars = len( str_ )

  if       val and not rdy:
    str_ = "#".ljust( nchars )
  elif not val and     rdy:
    str_ = " ".ljust( nchars )
  elif not val and not rdy:
    str_ = ".".ljust( nchars )

  return str_

def gen_msgs( nbits ):
  src_msgs  = []
  sink_msgs = []

  for i in xrange(10):
    x = random.randint(2, 2**nbits-1)
    y = random.randint(1, min(x, 2**(nbits/3*2)))
    src_msgs.append( (y << nbits) | x )
    sink_msgs.append( ((x / y) << nbits) | (x % y) )

  return src_msgs, sink_msgs

from pyrtl import *
from IntDivRem4 import IntDivRem4

# Setup pyrtl testing somehow

def run_sim( nbits, src_msgs, sink_msgs ):
  idiv = IntDivRem4( nbits )
  sim = Simulation()

  sim.step({
    idiv.reset: 1,
    idiv.req_val: 1,
    idiv.req_msg: 0,
    idiv.resp_rdy: 1,
  })

  cycle = 0
  src_msg = src_msgs.pop(0)

  print
  while (src_msgs or sink_msgs) and cycle < 5000:
    sim.step({
      idiv.reset: 0,
      idiv.req_val: 1,
      idiv.req_msg: src_msg,
      idiv.resp_rdy: 1,
    })

    req_rdy = sim.inspect(idiv.req_rdy)
    resp_val = sim.inspect(idiv.resp_val)

    if req_rdy and src_msgs:
      src_msg = src_msgs.pop(0)

    if resp_val and sink_msgs:
      sink_msg = sink_msgs.pop(0)
      assert sink_msg == sim.inspect(idiv.resp_msg)

    cycle += 1
    print "%d:" % cycle, valrdy_to_str( hex(sim.inspect(idiv.req_msg))[2:], \
                         sim.inspect(idiv.req_val), \
                         sim.inspect(idiv.req_rdy) ), ">>>",\
          valrdy_to_str( hex(sim.inspect(idiv.resp_msg))[2:], \
                         sim.inspect(idiv.resp_val), \
                         sim.inspect(idiv.resp_rdy) )

  reset_working_block()

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

def test_14():
  src_msgs, sink_msgs = gen_msgs( 14 )
  run_sim( 14, src_msgs, sink_msgs )

def test_64():
  src_msgs, sink_msgs = gen_msgs( 64 )
  run_sim( 64, src_msgs, sink_msgs )

def test_128():
  src_msgs, sink_msgs = gen_msgs( 128 )
  run_sim( 128, src_msgs, sink_msgs )
