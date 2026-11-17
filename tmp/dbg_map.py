import sys

sys.path.insert(0, ".")
import zone_v2 as Z

z = Z.Zone(sys.argv[1], verbose=False)
z.equal_instructions()
z.insert_random_nop(10)
blob = z._emit_text()

bad = 0
for n, item in enumerate(z.items):
    if item.old_rva is None:
        continue
    if z.map_point(item.old_rva) != item.new_rva:
        bad += 1
        if bad <= 5:
            print("MAPPATURA SBAGLIATA", hex(item.old_rva), "map", hex(z.map_point(item.old_rva)),
                  "new_rva", hex(item.new_rva), "index", n)
print("mappature sbagliate:", bad)
# la lista old_keys e' ordinata?
print("old_keys ordinati:", all(a < b for a, b in zip(z.old_keys, z.old_keys[1:])),
      "len", len(z.old_keys), "items", len(z.items))
# item non-insn con old_rva None in mezzo
none_positions = [n for n, it in enumerate(z.items) if it.old_rva is None]
print("item seq:", len(none_positions))
# verifica blob
pos = 0
for n, item in enumerate(z.items):
    if blob[pos:pos + len(item.new_bytes)] != item.new_bytes:
        print("blob mismatch at", n, item)
        break
    pos += len(item.new_bytes)
else:
    print("blob consistente")
