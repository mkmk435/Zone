import bisect
import sys

sys.path.insert(0, ".")
import zone_v2 as Z
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_GRP_JUMP, X86_GRP_CALL, X86_GRP_BRANCH_RELATIVE

z = Z.Zone(sys.argv[1], verbose=False)
z.equal_instructions()
z.insert_random_nop(10)
blob = z._emit_text()
image = z._build_image(blob)
z._patch_headers(image)
z._apply_patches(image)

print("delta", hex(z.delta), "content", hex(z.text_content_new_size),
      "rawlimit", hex(z.text_va + z.text_raw_size + z.delta),
      "text_end_old", hex(z.text_end_old))

cs = Cs(CS_ARCH_X86, CS_MODE_64)
cs.detail = True
errors = 0
for site, size, target, kind in z.branch_refs:
    if target is None:
        continue
    new_site = z.map_point(site)
    off = z.new_off(new_site)
    raw = bytes(image[off:off + 16])
    insn = None
    for i in cs.disasm(raw, new_site, 1):
        insn = i
        break
    ok = insn is not None and (X86_GRP_JUMP in insn.groups or X86_GRP_CALL in insn.groups
                               or X86_GRP_BRANCH_RELATIVE in insn.groups)
    if not ok:
        errors += 1
        if errors <= 6:
            pos = bisect.bisect_right(z.old_keys, site) - 1
            item = z.items[z.old_index[pos]]
            print("BAD site=%#x new=%#x off=%#x item=%r" % (site, new_site, off, item))
            print("    raw:", raw.hex(), "item bytes:", item.new_bytes.hex())
            print("    in text?", z.text_va <= new_site < z.text_va + z.text_raw_size + z.delta)
print("branch errors:", errors, "of", len(z.branch_refs))
