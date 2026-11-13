import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf86 import Zone
z = Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x86\windows_messagebox.bin")
sections, xrefs = z.analyze_data(timeout=30, print_strings=False, cache_path="data_cache.json", use_cache=True)
z.extract_data(sections, xrefs); z.finalize_data_refs()
print("extracted", z.extracted_data)
for f in z.data_ref_fixups:
    print({k:v for k,v in f.items() if k not in ("instr",)})
print("final_code_len", z.final_code_len, "pad", len(z.final_data_pad), "blob", len(z.final_data_blob))
