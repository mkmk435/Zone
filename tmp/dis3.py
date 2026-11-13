from capstone import *
code=open("tmp/mb_xd.bin","rb").read()
cs=Cs(CS_ARCH_X86,CS_MODE_64); cs.detail=True
ins=list(cs.disasm(code,0)); print(len(code),len(ins),sum(i.size for i in ins))
for i in ins[-40:]: print(f"{i.address:04x} {i.bytes.hex():<24} {i.mnemonic:<8} {i.op_str}")
