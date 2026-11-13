import sys, subprocess, time, ctypes
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf86 import Zone
from llm_payload import from_zone, assemble, validate

z = Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x86\windows_messagebox.bin")
sections, xrefs = z.analyze_data(timeout=30, print_strings=False, cache_path="data_cache.json", use_cache=True)
z.extract_data(sections, xrefs)
z.finalize_data_refs()
cp = from_zone(z, "x86")
print("=== SOURCE (first 40 lines) ===")
print("\n".join(cp.source.splitlines()[:40]))
print("=== DATA ===")
print(cp.data_source)
asm = assemble(cp.source, cp)
print("assembled", len(asm.payload), "code", asm.code_len, "blob", len(cp.blob))
rep = validate(asm, cp, technique="eq")
print(rep.summary(), rep.errors, rep.warnings[:5])
open("tmp/llm_roundtrip86.bin","wb").write(asm.payload)
