"""Biseziona i gruppi di patch: disabilita un parser e testa l'eseguibile."""
import sys

sys.path.insert(0, ".")
import zone_v2 as Z

groups = {
    "scan-ptrs": ["_parse_data_pointers"],
    "reloc": ["_parse_relocations"],
    "unwind": ["_parse_unwind_refs", "_parse_scope_tables", "_parse_cpp_eh"],
    "import": ["_parse_imports"],
    "dirs": ["_parse_exports", "_parse_resources", "_parse_debug", "_parse_tls",
             "_parse_load_config", "_parse_delay_imports"],
}

disable = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else []
methods = []
for name in disable:
    methods.extend(groups.get(name, []))


class Z2(Z.Zone):
    def insert_random_nop(self, probability=10):
        return 0

    def equal_instructions(self, probability=100):
        return 0

    def _build_items(self):
        super()._build_items()
        pad = 0x2000
        self.items.append(Z.Instruction("seq", None, pad, b"\x90" * pad))


for method in methods:
    setattr(Z2, method, lambda self, *a, **k: None)

z = Z2(sys.argv[1], seed=1, verbose=False)
z.write_pe_file(sys.argv[3])
print("scritto", sys.argv[3], "delta", hex(z.delta), "patch", len(z.patches))
