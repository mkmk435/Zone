import sys, re
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone, assemble, validate
z = Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections, xrefs = z.analyze_data(timeout=30, print_strings=False, cache_path="data_cache.json", use_cache=True)
z.extract_data(sections, xrefs); z.finalize_data_refs()
cp = from_zone(z, "x64")
lines = cp.source.splitlines()
out=[]; count=0; after_call=False
for line in lines:
    s=line.strip()
    # Never insert between a call and its RET label; never before a RET label
    if s.startswith("RET_"):
        out.append(line); after_call=True; continue
    if s and not s.startswith(";") and not s.endswith(":") and not after_call and count % 7 == 3:
        out.append("    nop")
    out.append(line)
    if s and not s.startswith(";") and not s.endswith(":"):
        after_call = s.lower().startswith("call")
        count += 1
src="\n".join(out)
asm=assemble(src, cp)
rep=validate(asm, cp, technique="nop")
print(rep.summary())
print("errors",rep.errors)
print("warnings",rep.warnings[:3])
open("tmp/llm_mock_nop.bin","wb").write(asm.payload)
