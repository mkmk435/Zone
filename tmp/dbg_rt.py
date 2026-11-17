import sys

sys.path.insert(0, ".")
import zone_v2 as Z

path = sys.argv[1]
z = Z.Zone(path, verbose=False)
z._layout()
blob = b"".join(i.new_bytes for i in z.items)
orig = bytes(z.data[z.text_raw_off:z.text_raw_off + z.text_raw_size])
print("len blob", len(blob), "len orig", len(orig), "delta", hex(z.delta))
if len(blob) != len(orig):
    print("length mismatch")
n = min(len(blob), len(orig))
first = None
diffs = 0
for i in range(n):
    if blob[i] != orig[i]:
        diffs += 1
        if first is None:
            first = i
print("diff bytes:", diffs, "first at rva", hex(z.text_va + first) if first is not None else None)
if first is not None:
    rva = z.text_va + first
    for item in z.items:
        if item.old_rva <= rva < item.old_rva + max(item.size, item.orig_size):
            print("item:", item.kind, hex(item.old_rva), "orig", item.orig_bytes.hex(),
                  "new", item.new_bytes.hex())
            break
    lo = max(0, first - 24)
    print("orig:", orig[lo:first + 24].hex())
    print("new :", blob[lo:first + 24].hex())
    # quanti item hanno new != orig
    bad = [(i.old_rva, i.kind) for i in z.items if i.new_bytes != i.orig_bytes[:len(i.new_bytes)]]
    print("item con byte diversi:", len(bad), [(hex(a), k) for a, k in bad[:10]])
