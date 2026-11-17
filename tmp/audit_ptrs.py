"""Audit: cerca puntatori rimasti 'vecchi' nell'immagine riscritta."""
import struct
import sys

sys.path.insert(0, ".")
import zone_v2 as Z


class Z2(Z.Zone):
    def insert_random_nop(self, probability=10):
        return 0

    def equal_instructions(self, probability=100):
        return 0

    def _build_items(self):
        super()._build_items()
        pad = 0x2000
        self.items.append(Z.Instruction("seq", None, pad, b"\x90" * pad))


z = Z2(sys.argv[1], seed=1, verbose=False)
blob = z._emit_text()
image = z._build_image(blob)
z._patch_headers(image)
z._apply_patches(image)
print("delta", hex(z.delta), "base", hex(z.image_base))

old = z.data
sections = [(s.Name.rstrip(b"\x00").decode(), s._zone_va, s._zone_vs) for s in z.sections]
new_sections = [(n, va + (z.delta if va > z.text_va else 0), vs) for n, va, vs in sections]
print("sezioni nuove:", [(n, hex(va), hex(vs)) for n, va, vs in new_sections])


def off_new(rva):
    return z.new_off(rva)


suspect8 = []
suspect4 = []
for name, va, vs in new_sections:
    if name == ".text":
        continue
    for delta_off in range(0, (vs & ~7), 8):
        site = va + delta_off
        off = off_new(site)
        if off is None or off + 8 > len(image):
            continue
        value = struct.unpack_from("<Q", image, off)[0]
        if value >= z.image_base:
            rva = value - z.image_base
            # puntatore a RVA che ora non e' piu' in una sezione coerente?
            target_section = None
            for n2, va2, vs2 in new_sections:
                if va2 <= rva < va2 + max(vs2, 0):
                    target_section = n2
            if target_section is None or (name == ".rdata" and target_section == ".text"):
                suspect8.append((name, hex(site), hex(rva), target_section))
        value4 = struct.unpack_from("<I", image, off)[0]
        if value4 and z.in_image_rva(value4):
            target_section = None
            for n2, va2, vs2 in new_sections:
                if va2 <= value4 < va2 + max(vs2, 0):
                    target_section = n2
            if target_section is None:
                suspect4.append((name, hex(site), hex(value4)))
print("puntatori 8 byte sospetti:", len(suspect8))
for s in suspect8[:20]:
    print("   ", s)
print("RVA 4 byte fuori sezione:", len(suspect4))
for s in suspect4[:20]:
    print("   ", s)
