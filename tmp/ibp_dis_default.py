from capstone import *
raw=open("tmp/real_ibp_msgbox_default.bin","rb").read()
n=308
cs=Cs(CS_ARCH_X86,CS_MODE_64); cs.detail=True
for i in cs.disasm(raw[:n],0):
    if i.mnemonic in ("jmp","call","ret","jne","je","jl","jrcxz","loop"):
        print(f"{i.address:04x} {i.mnemonic:<6} {i.op_str}")
