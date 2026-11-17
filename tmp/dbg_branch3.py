import bisect
import sys

sys.path.insert(0, ".")
import zone_v2 as Z
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_GRP_JUMP, X86_GRP_CALL, X86_GRP_BRANCH_RELATIVE

z = Z.Zone(sys.argv[1], seed=7, verbose=False)
z.equal_instructions()
z.insert_random_nop(10)
blob = z._emit_text()

cs = Cs(CS_ARCH_X86, CS_MODE_64)
cs.detail = True
errors = 0
for site, size, target, kind in z.branch_refs:
    if target is None:
        continue
    new_site = z.map_point(site)
    b = blob[new_site - z.text_va: new_site - z.text_va + 16]
    insn = None
    for i in cs.disasm(b, new_site, 1):
        insn = i
        break
    ok = insn is not None and (X86_GRP_JUMP in insn.groups or X86_GRP_CALL in insn.groups
                               or X86_GRP_BRANCH_RELATIVE in insn.groups)
    if not ok:
        errors += 1
        if errors <= 3:
            print("BAD site=%#x new=%#x" % (site, new_site))
            print("   recorded:", kind, "size", size, "target", hex(target))
            print("   insn in z.insns:", z.insns.get(site))
            print("   site e' item start?", site in set(z.old_keys))
            print("   blob:", b.hex())
            pos = bisect.bisect_right(z.old_keys, site) - 1
            item = z.items[z.old_index[pos]]
            print("   containing item:", item, hex(item.old_rva), "->", hex(item.new_rva),
                  item.new_bytes.hex())
print("errori:", errors)
