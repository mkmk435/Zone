from capstone import *
from capstone.x86 import *
from keystone import *
import sys
p = "original_pl/x64/windows_x64_messagebox.bin"
code = open(p,"rb").read()
cs = Cs(CS_ARCH_X86, CS_MODE_64); cs.detail=True
insns = list(cs.disasm(code,0))
print("bytes",len(code),"insns",len(insns),"covered",sum(i.size for i in insns))
for i in insns[:40]:
    print(f"{i.address:04x} {i.bytes.hex():<24} {i.mnemonic:<8} {i.op_str}")
