import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone
from keystone import *
z = Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections, xrefs = z.analyze_data(timeout=30, print_strings=False, cache_path="data_cache.json", use_cache=True)
z.extract_data(sections, xrefs); z.finalize_data_refs()
cp = from_zone(z, "x64")
full = cp.source + "\n" + cp.data_source
ks=Ks(KS_ARCH_X86,KS_MODE_64)
lines = full.splitlines()
# find first prefix that fails, but labels need definitions; use full and remove one line at a time to find culprit
for i, line in enumerate(lines):
    if not line.strip() or line.strip().startswith(";") or line.strip().endswith(":"):
        continue
    trial = lines[:i] + lines[i+1:]
    try:
        ks.asm("\n".join(trial),0)
    except Exception as e:
        print("REMOVING FIXES:", repr(line), "->", e)
        # not necessarily culprit
        break
# print lines around suspicious
for i,l in enumerate(lines):
    print(f"{i:3} {l}")
