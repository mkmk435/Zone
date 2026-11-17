import bisect
import sys

sys.path.insert(0, ".")
import zone_v2 as Z

path = sys.argv[1]
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
z = Z.Zone(path, seed=seed, verbose=False)
z.equal_instructions()
z.insert_random_nop(10)
blob = z._emit_text()
image = z._build_image(blob)
z._patch_headers(image)

item_offsets = []
for it in z.items:
    if it.kind != "insn" or not it.new_bytes:
        continue
    off = z.new_off(it.new_rva)
    item_offsets.append((off, off + len(it.new_bytes), it))
item_offsets.sort(key=lambda x: x[0])
starts = [x[0] for x in item_offsets]

hits = []
orig = z._write_value


def spy(img, new_rva, width, value):
    off = z.new_off(new_rva)
    p = bisect.bisect_right(starts, off) - 1
    if p >= 0:
        lo, hi, it = item_offsets[p]
        if lo <= off < hi:
            hits.append((hex(off), width, hex(value), hex(it.old_rva)))
    return orig(img, new_rva, width, value)


z._write_value = spy
z._apply_patches(image)
z._write_value = orig
print("scritture su codice:", len(hits))
for h in hits[:12]:
    print("  ", h)
