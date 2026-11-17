import sys

sys.path.insert(0, ".")
import zone_v2 as Z
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

z = Z.Zone(sys.argv[1], verbose=False)

with_rip = 0
detected = 0
missing = []
for rva, insn in z.insns.items():
    has = any(op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP for op in insn.operands)
    if has:
        with_rip += 1
item_map = {it.old_rva: it for it in z.items if it.kind == "insn"}
for rva, insn in z.insns.items():
    it = item_map.get(rva)
    if it is not None and it.rip_target is not None:
        detected += 1
    elif any(op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP for op in insn.operands):
        missing.append(rva)
print("istruzioni con operando RIP:", with_rip, "rilevate:", detected, "mancanti:", len(missing))
for rva in missing[:10]:
    insn = z.insns[rva]
    print("   ", hex(rva), insn.mnemonic, insn.op_str,
          "enc disp_off", insn.encoding.disp_offset, "disp_sz", insn.encoding.disp_size)
print("item con rip ma non in insns:",
      len([it for it in z.items if it.kind == "insn" and it.rip_target and it.old_rva not in z.insns]))
# istruzioni non decodificate che contengono FF 25 (call/jmp [rip])
