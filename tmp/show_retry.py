from capstone import *
raw=open("tmp/retry_out.bin","rb").read(); print(len(raw),raw.hex())
for i in Cs(CS_ARCH_X86,CS_MODE_64).disasm(raw,0): print(i.mnemonic,i.op_str)
