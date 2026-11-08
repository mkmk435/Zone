import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from capstone import *
raw = open(r"C:\Users\ubu\Desktop\Zone\tmp\x86_mb_xd.bin","rb").read()
print("size", len(raw))
cs = Cs(CS_ARCH_X86, CS_MODE_32); cs.detail = True
for start, end in ((0x8f, 0xa8), (0xba, 0xc8), (0xee, 0x118)):
    print(f"--- 0x{start:x}..0x{end:x}")
    for i in cs.disasm(raw[start:end], start):
        print(f"  0x{i.address:03x} {i.bytes.hex(' '):<24s} {i.mnemonic} {i.op_str}")
