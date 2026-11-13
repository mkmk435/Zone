import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone, assemble, validate

z = Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections, xrefs = z.analyze_data(timeout=30, print_strings=False,
                                 cache_path="data_cache.json", use_cache=True)
z.extract_data(sections, xrefs)
z.finalize_data_refs()
cp = from_zone(z, "x64")
print("=== CANONICAL SOURCE ===")
print(cp.source)
print("=== DATA SOURCE ===")
print(cp.data_source)
asm = assemble(cp.source, cp)
print("assembled", len(asm.payload), "code", asm.code_len, "blob", len(cp.blob))
rep = validate(asm, cp, technique="eq")
print(rep.summary())
print("errors", rep.errors)
print("warnings", rep.warnings[:5])
open("tmp/llm_roundtrip.bin","wb").write(asm.payload)
