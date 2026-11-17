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

target_item = None
pos = 0
for n, item in enumerate(z.items):
    if item.kind == "insn" and item.new_bytes:
        off = z.new_off(item.new_rva)
        cur = bytes(image[off:off + len(item.new_bytes)])
        if cur != item.new_bytes:
            target_item = (n, item, off)
            break
print("prima patch, item gia' diverso:", target_item is not None)
if target_item:
    print("   ", target_item[1], hex(target_item[2]))
# NB: prima di applicare le patch l'immagine dovrebbe combaciare

writes = []
orig = z._write_value


def spy(img, new_rva, width, value):
    writes.append((new_rva, width, value))
    return orig(img, new_rva, width, value)


z._write_value = spy
z._apply_patches(image)
z._write_value = orig

import bisect
item_starts = [(it.new_rva, it) for it in z.items if it.kind == "insn"]
starts = [x[0] for x in item_starts]
inside = {}
for new_rva, width, value in writes:
    p = bisect.bisect_right(starts, new_rva) - 1
    if p < 0:
        continue
    it = item_starts[p][1]
    if it.new_rva <= new_rva < it.new_rva + it.size:
        inside.setdefault((it.old_rva, it.mnemonic if hasattr(it, 'mnemonic') else '?'), 0)
        inside[(it.old_rva, it.cs_insn.mnemonic)] = inside.get((it.old_rva, it.cs_insn.mnemonic), 0) + 1
print("scritture dentro istruzioni:", sum(inside.values()), "su", len(writes))
for k, v in list(inside.items())[:10]:
    print("   ", hex(k[0]), k[1], v)
# chi ha scritto nell'item 0x15d02?
for new_rva, width, value in writes:
    if 0x18e81 <= new_rva < 0x18e81 + 8:
        print("write dentro l'item:", hex(new_rva), width, hex(value))
