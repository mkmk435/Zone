import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf86 import Zone
from llm_payload import from_zone
z = Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x86\windows_messagebox.bin")
sections, xrefs = z.analyze_data(timeout=30, print_strings=False, cache_path="data_cache.json", use_cache=True)
z.extract_data(sections, xrefs); z.finalize_data_refs()
cp = from_zone(z, "x86")
lines = cp.source.splitlines()
# insert a nop after _start and one in the middle of a safe sequence
out=[]
for i,line in enumerate(lines):
    out.append(line)
    if line.strip() == "_start:":
        out.append("    nop")
src="```asm\n"+"\n".join(out)+"\n```\n"
open("tmp/mock_nop86.txt","w",encoding="utf-8").write(src)
print("canonical lines",len(lines))
