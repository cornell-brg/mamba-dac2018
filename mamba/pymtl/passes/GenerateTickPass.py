#-------------------------------------------------------------------------
# GenerateTickPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass
import ast, py

class GenerateTickPass( BasePass ):
  def __init__( self, mode='unroll', dump=False ):
    self.mode = mode
    self.dump = dump

  def apply( self, m ):
    if not hasattr( m, "_serial_schedule" ):
      raise PassOrderError( "_serial_schedule" )

    self.generate_tick_func( m )

  # After we come up with a schedule, we generate a tick function that calls
  # all update blocks. We can do "JIT" here.

  def generate_tick_func( self, m ):
    assert self.mode in [ 'normal', 'unroll' ]

    schedule = m._serial_schedule
    assert schedule, "No update block found in the model"

    if self.mode == 'normal':
      gen_tick_src = """
      def tick_normal():
        for blk in schedule:
          blk()
      """
      def tick_normal():
        for blk in schedule:
          blk()

      ret = tick_normal

    if self.mode == 'unroll': # Berkin's recipe
      strs = map( "  update_blk{}() # {}".format, xrange( len(schedule) ), \
                                                [ x.__name__ for x in schedule ] )
      gen_tick_src = """
        {}
        def tick_unroll():
          # The code below does the actual calling of update blocks.
          {}""".format( "; ".join( map(
                    "update_blk{0} = schedule[{0}]".format,
                        xrange( len( schedule ) ) ) ),
                    "\n          ".join( strs ) )

      exec py.code.Source( gen_tick_src ).compile() in locals()
      ret = tick_unroll

    m._tick_src = gen_tick_src
    m.tick = ret
