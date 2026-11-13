import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone
z=Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections,xrefs=z.analyze_data(timeout=30,print_strings=False,cache_path="data_cache.json",use_cache=True)
z.extract_data(sections,xrefs); z.finalize_data_refs()
cp=from_zone(z,"x64")
lines=cp.source.splitlines()
out=[]
for line in lines:
    out.append(line)
    if line.strip()=="_start:":
        out.append("    nop")
open("tmp/mock_nop64.txt","w",encoding="utf-8").write("```asm\n"+"\n".join(out)+"\n```\n")
