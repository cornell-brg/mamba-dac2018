import random
random.seed(0xdeadbeee)

from pymtl import *
from pclib.rtl import TestSourceValRdy, TestSinkValRdy
from pclib.ifcs import InValRdyIfc, OutValRdyIfc
from IntDivRem4 import IntDivRem4

class TestHarness( RTLComponent ):

  def __init__( s, cls, nbits, src_msgs, sink_msgs ):

    s.src  = TestSourceValRdy( mk_bits(nbits*2), src_msgs )
    s.sink = TestSinkValRdy( mk_bits(nbits*2), sink_msgs )

    s.imul = cls(nbits)( req = s.src.out, resp = s.sink.in_ )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.imul.line_trace()+" >>> "+s.sink.line_trace()

def run_test( model ):
  SimRTLPass().apply( model )
  # PrintMetadataPass().apply( th )
  T, maxT = 0, 5000

  print
  while not model.done():
    model.tick()
    print "{}: {}".format( T, model.line_trace() )
    T += 1
    assert T < maxT

def gen_msgs( nbits ):
  src_msgs  = []
  sink_msgs = []

  for i in xrange(10):
    x = random.randint(2, 2**nbits-1)
    y = random.randint(1, min(x, 2**(nbits/3*2)))
    z = Bits(nbits*2,0)
    z[0:nbits]  = x
    z[nbits:nbits*2] = y
    src_msgs.append( z )
    sink_msgs.append( Bits(nbits*2, ((x / y) << nbits) | (x % y) ) )

  return src_msgs, sink_msgs

def test_4():
  src_msgs, sink_msgs = gen_msgs( 4 )
  run_test( TestHarness( IntDivRem4, 4,
                         src_msgs, sink_msgs ) )

def test_64():
  src_msgs, sink_msgs = gen_msgs( 64 )
  run_test( TestHarness( IntDivRem4, 64,
                         src_msgs, sink_msgs ) )
def test_128():
  src_msgs, sink_msgs = gen_msgs( 128 )
  run_test( TestHarness( IntDivRem4, 128,
                         src_msgs, sink_msgs ) )

