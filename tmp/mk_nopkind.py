import sys

sys.path.insert(0, ".")
import zone_v2 as Z

# forza un solo tipo di sequenza nop per capire quale rompe
kind = sys.argv[2]
seqs = {
    "pushfq": b"\x9c\x90\x90\x9d",
    "mov": None,      # mov r9,r9  (nessun flag, nessuno stack)
    "lea": None,
    "or": None,
}


class Z2(Z.Zone):
    def _nop_sequence(self):
        if kind == "pushfq":
            return bytearray(b"\x9c\x90\x90\x9d")
        if kind == "mov":
            enc, _ = self.ks.asm("mov r9,r9", 0)
            return bytearray(enc)
        if kind == "lea":
            enc, _ = self.ks.asm("lea r9,[r9+0]", 0)
            return bytearray(enc)
        if kind == "or":
            enc, _ = self.ks.asm("or r9,r9", 0)
            return bytearray(enc)
        if kind == "push":
            enc, _ = self.ks.asm("push r9;pop r9", 0)
            return bytearray(enc)
        raise SystemExit("tipo sconosciuto")


z = Z2(sys.argv[1], seed=7, verbose=False)
z.insert_random_nop(probability=10)
z.write_pe_file(sys.argv[3])
print("scritto", sys.argv[3], "delta", hex(z.delta))
