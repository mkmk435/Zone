import os, sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
os.chdir(r"C:\Users\ubu\Desktop\Zone")
from capstone import *
raw = open(r"original_pl\x86\windows_messagebox.bin","rb").read()
cs = Cs(CS_ARCH_X86, CS_MODE_32); cs.detail = True
print("bytes 0x90..0xa5:", raw[0x90:0xa5].hex(" "))
for i in cs.disasm(raw[0x8f:0xa8], 0x8f):
    print(f"  0x{i.address:03x} {i.bytes.hex(' '):<24s} {i.mnemonic} {i.op_str}")
