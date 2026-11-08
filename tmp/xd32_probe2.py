import contextlib
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import pobf86
from capstone import x86_const

path = os.path.join("original_pl", "x86", "windows_messagebox.bin")
raw = open(path, "rb").read()
print("first 48 bytes:", raw[:48].hex(" "))

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    z = pobf86.Zone(path)

print("\nlinear sweep around offset 0..0x20:")
for ins in z.instructions:
    if ins.original_instruction.address > 0x20:
        break
    print(f"  0x{ins.original_instruction.address:03x}  {ins.original_instruction.bytes.hex(' '):<20s} "
          f"{ins.original_instruction.mnemonic} {ins.original_instruction.op_str}")

print("\ncall/pop pairs with a nonzero gap (what extract_data32 would move):")
index = 0
while index < len(z.instructions):
    instr = z.instructions[index]
    ci = instr.new_instruction
    if ci.mnemonic == "call" and ci.operands and ci.operands[0].type == x86_const.X86_OP_IMM:
        target_index = next((j for j in range(index + 1, len(z.instructions))
                             if z.instructions[j].new_instruction.address == ci.operands[0].imm), None)
        if target_index is not None:
            target = z.instructions[target_index]
            gap = target.new_instruction.address - (ci.address + ci.size)
            print(f"  call at 0x{ci.address:03x} ({ci.bytes.hex(' ')}) -> 0x{ci.operands[0].imm:03x} "
                  f"= {target.new_instruction.mnemonic} {target.new_instruction.op_str} "
                  f"(gap={gap} bytes)")
    index += 1
