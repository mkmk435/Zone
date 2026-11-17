import sys

sys.path.insert(0, ".")
import zone_v2 as Z

z = Z.Zone(sys.argv[1], verbose=False)
z.equal_instructions()
z.insert_random_nop(10)
blob = z._emit_text()

pos = 0
for n, item in enumerate(z.items):
    expected = item.new_rva - z.text_va
    if pos != expected:
        print("shift al item", n, item, "pos", hex(pos), "atteso", hex(expected),
              "delta", pos - expected)
        for j in range(max(0, n - 3), min(len(z.items), n + 2)):
            it = z.items[j]
            print("   ", j, it, "size", it.size, "len(new_bytes)", len(it.new_bytes))
        break
    pos += len(item.new_bytes)
else:
    print("nessuno shift, totale", hex(pos))
