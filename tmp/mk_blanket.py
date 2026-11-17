"""Variante B: shift + patch normali + regola "blanket" per ogni RVA nei dati."""
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

    def _parse_data_refs(self):
        super()._parse_data_refs()
        # regola brute force: ogni dword che punta a una sezione spostata
        lo = None
        for s in self.moved_sections:
            if lo is None or s._zone_va < lo:
                lo = s._zone_va
        hi = self.pe.OPTIONAL_HEADER.SizeOfImage
        added = 0
        for s in self.moved_sections:
            size = s._zone_vs & ~3
            blob = self.read(s._zone_va, size) or b""
            import struct
            for offset in range(0, len(blob) - 3, 4):
                site = s._zone_va + offset
                if site in self.data_patch_sites:
                    continue
                value = struct.unpack_from("<I", blob, offset)[0]
                if lo <= value < hi:
                    self._note_patch(site, 4, "rva", value)
                    added += 1
        print("blanket: +%d patch" % added)


z = Z2(sys.argv[1], seed=1, verbose=False)
z.write_pe_file(sys.argv[3])
print("scritto", sys.argv[3], "delta", hex(z.delta), "patch", len(z.patches))
