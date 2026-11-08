import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from capstone import *
raw = open(r"C:\Users\ubu\Desktop\Zone\original_pl\x86\windows_messagebox.bin","rb").read()
cs = Cs(CS_ARCH_X86, CS_MODE_32)
for start in (0xa6, 0xd5):
    print(f"--- from 0x{start:x}")
    for i in cs.disasm(raw[start:start+0x30], start):
        print(f"  0x{i.address:03x} {i.bytes.hex(' '):<22s} {i.mnemonic} {i.op_str}")
