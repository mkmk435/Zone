import bisect
import sys

sys.path.insert(0, ".")
import zone_v2 as Z

z = Z.Zone(sys.argv[1], verbose=False)
z.equal_instructions()
z.insert_random_nop(10)
blob = z._emit_text()
image = z._build_image(blob)

site = 0x18a5b
pos = bisect.bisect_right(z.old_keys, site) - 1
item = z.items[z.old_index[pos]]
print("item", item, "old", hex(item.old_rva), "new", hex(item.new_rva),
      "size", item.size, "bytes", item.new_bytes.hex())
b_off = item.new_rva - z.text_va
print("blob at item:", blob[b_off:b_off + 8].hex())
i_off = z.new_off(item.new_rva)
print("image off", hex(i_off), "image at item:", bytes(image[i_off:i_off + 8]).hex())
print("blob len", len(blob), "image len", len(image), "text_raw_off", hex(z.text_raw_off))
# dove sta davvero la sequenza nel blob?
needle = item.new_bytes
idx = blob.find(needle)
print("prima occorrenza della sequenza nel blob:", hex(idx) if idx >= 0 else None,
      "attesa", hex(b_off))
print("image find:", image.find(needle))
print("offset atteso in image:", hex(z.text_raw_off + b_off))
