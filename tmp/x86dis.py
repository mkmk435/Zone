from capstone import *
raw=open("tmp/x86_mb_xd2.bin","rb").read()
print("size",len(raw))
cs=Cs(CS_ARCH_X86,CS_MODE_32); cs.detail=True
print("--- code 0..0xe7")
for i in cs.disasm(raw[:231],0): print(f"{i.address:04x} {i.bytes.hex():<18} {i.mnemonic:<8} {i.op_str}")
print("--- blob 0xf0..")
for i in cs.disasm(raw[0xf0:],0xf0): print(f"{i.address:04x} {i.bytes.hex():<18} {i.mnemonic:<8} {i.op_str}")
