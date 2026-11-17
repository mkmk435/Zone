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
z._patch_jump_tables(image)

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
    if insn is None or not (X86_GRP_JUMP in insn.groups or X86_GRP_CALL in insn.groups
                            or X86_GRP_BRANCH_RELATIVE in insn.groups):
        errors += 1
        if errors <= 5:
            item = z.items[z.old_index[max(0, __import__("bisect").bisect_right(z.old_keys, site) - 1)]]
            print("BAD site=%#x new=%#x kind=%s" % (site, new_site, kind))
            print("   raw at new:", raw.hex())
            print("   item:", item, "size", item.size, "orig", item.orig_bytes.hex(),
                  "new_bytes", item.new_bytes.hex())
            print("   item.new_rva", hex(item.new_rva))
print("branch errors:", errors, "of", len(z.branch_refs))
