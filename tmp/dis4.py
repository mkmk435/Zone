from capstone import *
code=open("tmp/mb_xd.bin","rb").read()[:313]
cs=Cs(CS_ARCH_X86,CS_MODE_64); cs.detail=True
for i in cs.disasm(code,0):
    if 0xc0 <= i.address <= 0x140:
        print(f"{i.address:04x} {i.bytes.hex():<24} {i.mnemonic:<8} {i.op_str}")
