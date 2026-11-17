import sys
sys.path.insert(0,".")
import zone
z = zone.Zone(sys.argv[1], verbose=False)
r,b,s = z.coverage()
print("copertura %.2f%% blocchi %d byte %d" % (r*100,b,s))
# stampa solo i blocchi che la nuova coverage considera sospetti
targets = set()
for it in z.items:
    if it.is_branch and it.target_old is not None: targets.add(it.target_old)
    if it.rip_target is not None: targets.add(it.rip_target)
    if it.abs_target is not None: targets.add(it.abs_target)
targets.update(getattr(z, "jumptable_entries", {}))
for f in z.runtime_functions: targets.add(f["begin"])
targets.add(z.pe.OPTIONAL_HEADER.AddressOfEntryPoint)
import bisect
st = sorted(targets)
for idx, it in enumerate(z.items):
    if it.kind != "data" or it.old_rva is None: continue
    if it.old_rva >= z.text_rva_end_vsize: continue
    if z._is_padding_block(it): continue
    if any(lo <= it.old_rva < hi for lo,hi in z.jumptable_ranges): continue
    lo,hi = it.old_rva, it.old_rva+it.size
    p = bisect.bisect_left(st, lo)
    reach = p < len(st) and st[p] < hi
    prev = z.items[idx-1] if idx else None
    ft = bool(prev and prev.kind=="insn" and prev.old_rva is not None
              and prev.old_rva+prev.orig_size==lo
              and not z._block_ends_unconditionally([prev]))
    print("%#x size %-4d reach=%s fallthrough=%s prev=%s" % (lo, it.size, reach, ft,
          (prev.cs_insn.mnemonic + " " + prev.cs_insn.op_str) if prev and prev.kind=="insn" else prev))
    for insn in list(z.cs.disasm(it.data[:40], lo))[:8]:
        print("      %#x %-22s %s %s" % (insn.address, insn.bytes.hex(), insn.mnemonic, insn.op_str))
