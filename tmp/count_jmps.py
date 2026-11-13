import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone
from capstone import *
z=Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections,xrefs=z.analyze_data(timeout=30,print_strings=False,cache_path="data_cache.json",use_cache=True)
z.extract_data(sections,xrefs); z.finalize_data_refs()
cp=from_zone(z,"x64")
cs=Cs(CS_ARCH_X86,CS_MODE_64)
def jmps(code):
    return [(i.address,i.op_str) for i in cs.disasm(code,0) if i.mnemonic=="jmp"]
print("original jmps", len(jmps(cp.code)))
for p,n in (("tmp/real_ibp_msgbox_default.bin",308),("tmp/real_ibp_msgbox.bin",312)):
    raw=open(p,"rb").read()[:n]
    print(p, "jmps",len(jmps(raw)), jmps(raw))
