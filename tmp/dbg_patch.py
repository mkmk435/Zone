import sys

sys.path.insert(0, ".")
import zone_v2 as Z

z = Z.Zone(sys.argv[1], verbose=False)
z.equal_instructions()
z.insert_random_nop(10)
blob = z._emit_text()
image = z._build_image(blob)

# 1) i byte degli item devono stare esattamente a new_off(new_rva)
bad = 0
for item in z.items[:]:
    if item.kind != "insn":
        continue
    off = z.new_off(item.new_rva)
    if bytes(image[off:off + len(item.new_bytes)]) != item.new_bytes:
        bad += 1
        if bad <= 3:
            print("MISMATCH", hex(item.old_rva), "new", hex(item.new_rva), "off", hex(off))
print("item mismatch prima delle patch:", bad)

# 2) quali patch scrivono dentro la zona codice?
before = bytes(image)
z._apply_patches(image)
after = bytes(image)
changed = [i for i in range(len(before)) if before[i] != after[i]]
print("byte cambiati dalle patch:", len(changed))
lo = z.text_raw_off
hi = z.text_raw_off + z.text_raw_size + z.delta
inside = [c for c in changed if lo <= c < hi]
print("di cui dentro .text:", len(inside))
if inside:
    for c in inside[:10]:
        print("  off", hex(c), "rva", hex(c - z.text_raw_off + z.text_va),
              "old", before[c:c + 8].hex(), "new", after[c:c + 8].hex())
# 3) ricontrolla i branch
bad2 = 0
for item in z.items:
    if item.kind != "insn" or not item.is_branch:
        continue
    off = z.new_off(item.new_rva)
    if bytes(image[off:off + len(item.new_bytes)]) != item.new_bytes:
        bad2 += 1
print("branch sovrascritti dalle patch:", bad2)
