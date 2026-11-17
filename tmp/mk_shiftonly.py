import sys

sys.path.insert(0, ".")
import zone_v2 as Z


class Z2(Z.Zone):
    """Nessuna modifica al codice: aggiunge solo padding in coda alla .text."""

    def insert_random_nop(self, probability=10):
        return 0

    def equal_instructions(self, probability=100):
        return 0

    def _build_items(self):
        super()._build_items()
        pad = int(sys.argv[2], 0)
        chunk = Z.Instruction("seq", None, pad, b"\x90" * pad)
        self.items.append(chunk)


z = Z2(sys.argv[1], seed=7, verbose=False)
z.write_pe_file(sys.argv[3])
print("delta", hex(z.delta), "scritto", sys.argv[3])
