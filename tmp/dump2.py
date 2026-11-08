import os, sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
os.chdir(r"C:\Users\ubu\Desktop\Zone")
from capstone import *
raw = open(r"original_pl\x86\windows_messagebox.bin","rb").read()
cs = Cs(CS_ARCH_X86, CS_MODE_32)
for start in (0x95, 0xa6, 0xd6):
    print(f"--- from 0x{start:x}")
    for i in cs.disasm(raw[start:start+0x28], start):
        print(f"  0x{i.address:03x} {i.bytes.hex(' '):<20s} {i.mnemonic} {i.op_str}")
