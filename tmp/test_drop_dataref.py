import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone, assemble, validate
z=Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections,xrefs=z.analyze_data(timeout=30,print_strings=False,cache_path="data_cache.json",use_cache=True)
z.extract_data(sections,xrefs); z.finalize_data_refs()
cp=from_zone(z,"x64")
src=cp.source.replace("    lea rcx, [rip + DATA_0]\n","")
asm=assemble(src,cp)
rep=validate(asm,cp,technique="eq",min_similarity=None)
print(rep.ok); print(rep.errors)
