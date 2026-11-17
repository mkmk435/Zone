import sys

sys.path.insert(0, ".")
import zone_v2 as Z
from capstone import CS_ARCH_X86, CS_MODE_64, Cs

z = Z.Zone(sys.argv[1], verbose=False)
cs = Cs(CS_ARCH_X86, CS_MODE_64)
cs.detail = True

# riferimenti lea rip -> dentro .text che non sono istruzioni note
lea_targets = {}
for rva, insn in z.insns.items():
    for op in insn.operands:
        if op.type == 3 and op.mem.base == 41:  # RIP
            target = insn.address + insn.size + op.mem.disp
            if z.text_va <= target < z.text_rva_end_vsize and target not in z.insns:
                lea_targets.setdefault(target, []).append(rva)

data_blocks = [it for it in z.items if it.kind == "data" and it.old_rva < z.text_rva_end_vsize]
print("blocchi dati in .text:", len(data_blocks), "byte:",
      sum(it.size for it in data_blocks), "di", z.text_vsize)
print("target lea (rip) non decodificati:", len(lea_targets))
withmov = sum(1 for rva, insn in z.insns.items() if insn.id == 1)  # X86_INS_CALL
big = sorted(data_blocks, key=lambda it: -it.size)[:12]
for it in big:
    head = it.data[:24].hex()
    print("%#x  size %#x  refs-lea %d  %s" % (it.old_rva, it.size,
                                              len(lea_targets.get(it.old_rva, [])), head))
    for insn in list(cs.disasm(it.data[:48], it.old_rva))[:6]:
        print("      %#x %-20s %s %s" % (insn.address, insn.bytes.hex(), insn.mnemonic, insn.op_str))
