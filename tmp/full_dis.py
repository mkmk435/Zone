import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from capstone import *
raw = open(r"C:\Users\ubu\Desktop\Zone\original_pl\x86\windows_messagebox.bin","rb").read()
cs = Cs(CS_ARCH_X86, CS_MODE_32)
for i in cs.disasm(raw[0x95:], 0x95):
    print(f"0x{i.address:03x} {i.bytes.hex(' '):<24s} {i.mnemonic} {i.op_str}")
