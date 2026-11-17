import sys
sys.path.insert(0,".")
import zone
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
z = zone.Zone("ploader.exe", verbose=False)
cs = Cs(CS_ARCH_X86, CS_MODE_64); cs.detail=True
susp = []
for it in z.items:
    if it.kind != "data" or it.old_rva is None: continue
    if it.old_rva >= z.text_rva_end_vsize: continue
    if it.data and it.data[0] in (0xCC,0x00,0x90): continue
    susp.append(it)
print("sospetti:", len(susp), "byte:", sum(i.size for i in susp))
for it in susp[:22]:
    print("%#x size %-4d %s" % (it.old_rva, it.size, it.data[:16].hex()))
