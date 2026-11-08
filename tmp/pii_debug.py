import contextlib
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import pobf86

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    z = pobf86.Zone(os.path.join("original_pl", "x86", "windows_messagebox.bin"))
    sections, xrefs = z.analyze_data(timeout=20, print_strings=False, use_cache=True)
    z.extract_data(sections, xrefs)
    z.create_label_table()
    z.pii_dispatcher_v2()

total = sum(len(i.new_instruction.bytes) for i in z.instructions)
stub = [i for i in z.instructions if i.new_instruction.mnemonic == "pop"
        and i.new_instruction.op_str == "eax"]
print("total bytes:", total, hex(total))
print("mem_address:", z.mem_address, hex(z.mem_address))
print("delta:", total - z.mem_address)
print("last 6 insns:")
for i in z.instructions[-6:]:
    print("  ", hex(i.new_instruction.address), len(i.new_instruction.bytes),
          i.new_instruction.mnemonic, i.new_instruction.op_str)
