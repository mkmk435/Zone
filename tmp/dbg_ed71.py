import sys
sys.path.insert(0,".")
import zone_v2 as Z
z = Z.Zone("ploader.exe", verbose=False)
item = {it.old_rva: it for it in z.items if it.kind=="insn"}
for rva in (0xed71, 0xed72, 0xed77):
    print(hex(rva), "in insns:", rva in z.insns, "item:", item.get(rva))
it = item.get(0xed71)
if it:
    print("  rip_target", hex(it.rip_target) if it.rip_target else None, "disp_off", it.disp_off, "size", it.size)
    print("  bytes", it.orig_bytes.hex())
# in che blocco sta?
import bisect
pos = bisect.bisect_right(z.old_keys, 0xed71) - 1
blk = z.items[z.old_index[pos]]
print("blocco contenitore:", blk, "old", hex(blk.old_rva), "size", blk.size)
