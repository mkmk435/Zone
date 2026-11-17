import sys

sys.path.insert(0, ".")
import zone

z = zone.Zone(sys.argv[1], verbose=False)
susp = []
for it in z.items:
    if it.kind != "data" or it.old_rva is None:
        continue
    if it.old_rva >= z.text_rva_end_vsize:
        continue
    if it.data and it.data[0] in (0xCC, 0x00, 0x90):
        continue
    susp.append(it)

print("blocchi sospetti:", len(susp))
for it in susp:
    lo, hi = it.old_rva, it.old_rva + it.size
    # chi punta dentro?
    refs = []
    for rva, insn in z.insns.items():
        for op in insn.operands:
            if op.type == 3 and op.mem.base == 41:      # rip
                t = insn.address + insn.size + op.mem.disp
                if lo <= t < hi:
                    refs.append(("rip", rva, t))
        if op.type == 2 and insn.mnemonic == "mov":     # imm
            t = op.imm & 0xffffffff
            if lo <= t < hi:
                refs.append(("imm", rva, t))
        if insn.is_branch if hasattr(insn, "is_branch") else False:
            pass
    for site, size, target, kind in z.branch_refs:
        if target is not None and lo <= target < hi:
            refs.append((kind, site, target))
    # fallthrough dal blocco precedente?
    fallthrough = False
    for item in z.items:
        if item.old_rva is None or item.kind != "insn":
            continue
        end = item.old_rva + item.orig_size
        if end == lo:
            fallthrough = not z._block_ends_unconditionally([item])
    # entry delle tabelle
    table = [e for e in getattr(z, "jumptable_entries", {})
             if lo <= e < hi]
    print("%#x size %-4d fallthrough=%s refs=%s table_entries=%d" %
          (lo, it.size, fallthrough, refs[:4], len(table)))
    for insn in list(z.cs.disasm(it.data[:32], lo))[:5]:
        print("      %#x %-20s %s %s" % (insn.address, insn.bytes.hex(),
                                         insn.mnemonic, insn.op_str))
