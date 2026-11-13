import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone, assemble
from keystone import *
z = Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections, xrefs = z.analyze_data(timeout=30, print_strings=False, cache_path="data_cache.json", use_cache=True)
z.extract_data(sections, xrefs)
z.finalize_data_refs()
cp = from_zone(z, "x64")
open("tmp/canon_full.asm","w").write(cp.source + "\n" + cp.data_source)
ks=Ks(KS_ARCH_X86,KS_MODE_64)
for line in (cp.source + "\n" + cp.data_source).splitlines():
    s=line.strip()
    if not s or s.startswith(";") or s.endswith(":"):
        continue
    try:
        ks.asm(line,0)
    except Exception as e:
        print("FAIL LINE:", repr(line), "->", e)
