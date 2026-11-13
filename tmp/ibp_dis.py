from capstone import *
raw=open("tmp/real_ibp_msgbox.bin","rb").read()
code=raw[:312]
cs=Cs(CS_ARCH_X86,CS_MODE_64); cs.detail=True
ins=list(cs.disasm(code,0))
print("insns",len(ins),"covered",sum(i.size for i in ins))
# print all jmp/call/ret and labels implied
for i in ins:
    if i.mnemonic in ("jmp","ret","call","jne","je","jl","jrcxz","loop"):
        print(f"{i.address:04x} {i.mnemonic:<6} {i.op_str}")
