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
z._apply_patches(image)
after = bytes(image)

pos = 0
for n, item in enumerate(z.items):
    if item.kind == "insn" and item.new_bytes:
        off = z.new_off(item.new_rva)
        got = after[off:off + len(item.new_bytes)]
        if got != item.new_bytes:
            print("primo item corrotto: index", n, item, "old", hex(item.old_rva),
                  "new", hex(item.new_rva), "size", item.size,
                  "len(new_bytes)", len(item.new_bytes))
            print("   atteso:", item.new_bytes.hex())
            print("   immagine:", got.hex())
            for j in range(max(0, n - 6), n + 1):
                it = z.items[j]
                print("   ", j, it, "size", it.size, "len", len(it.new_bytes),
                      "old", hex(it.old_rva) if it.old_rva else None)
            break
