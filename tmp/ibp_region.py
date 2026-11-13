from capstone import *
raw=open("tmp/real_ibp_msgbox.bin","rb").read()[:312]
cs=Cs(CS_ARCH_X86,CS_MODE_64); cs.detail=True
for i in cs.disasm(raw,0):
    if 0x10 <= i.address <= 0x60:
        print(f"{i.address:04x} {i.bytes.hex():<20} {i.mnemonic:<8} {i.op_str}")
