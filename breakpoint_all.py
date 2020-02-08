#=========================================================================
# Set a breakpoint to all user-space functions
#=========================================================================
# A quick-and-dirty script for tracing an application.
#
# source: https://blog.0x972.info/?d=2017/02/10/08/25/23-gdb-please-set-a-breakpoint-on-all-my-functions

import gdb

def get_file_addresses():
  sources = gdb.execute("info sources", to_string=True).split("\n")
  assert "Source files for which symbols have been read in" in sources[0]

  for line in sources:
    if line.startswith("Source files ") or not line.strip():
      continue

    for source in line.split(", "):
      try:
        # fails if source is a header file
        bpt_msg = gdb.execute("break {}:1".format(source), to_string=True)
      except gdb.error as e:
        # if show breakpoint pending ==> off
        continue

      bp_id = bpt_msg.partition("Breakpoint ")[-1].partition(" ")[0]
      gdb.execute("delete {}".format(bp_id), to_string=True)

      if "pending" in bpt_msg or "No line" in bpt_msg:
        # if show breakpoint pending ==> on
        """No line 1 in file "/usr/include/bits/pthreadtypes.h".
        Breakpoint 8 (/usr/include/bits/pthreadtypes.h:1) pending."""
        continue

      """Note: breakpoint 3 also set at pc 0x400a57.
      Breakpoint 4 at 0x400a57: file chopsticks.c, line 1."""

      bp_line = [a for a in bpt_msg.split("\n") if a.startswith("Breakpoint ")][0]
      file_1st_addr = int(bp_line.split(" ")[3][:-1], 16)

      yield source, file_1st_addr


def get_all_functions_from_pc(pc):
  block = gdb.block_for_pc(pc)
  for symb in block.global_block:
    if not symb.is_function: continue

    yield symb


def set_trace_bpt_on_all_symbols():
  for source, pc in get_file_addresses():
    print("{} ==> {}".format(source, hex(pc)))
    for fct_symb in get_all_functions_from_pc(pc):
      bpt = TraceBreakpoint(fct_symb)
      print("\t{} (Bpt #{})".format(fct_symb, bpt.number))


class TraceBreakpoint(gdb.Breakpoint):
  def __init__(self, symb):
    addr = int(str(symb.value().address).split()[0],0)
    gdb.Breakpoint.__init__(self, "*{}".format(hex(addr)), internal=True)

  def stop(self):
    caller = gdb.newest_frame().older()
    caller_name = caller.name() if caller else 'none'
    print('{};{};{}'.format(gdb.selected_thread().num, caller_name, gdb.newest_frame().name()))

    return False

if __name__ == "__main__":
  set_trace_bpt_on_all_symbols()

  print("Consider setting non-stop mode in multithreaded environments: set non-stop on")

