from capstone import *
code=open("tmp/llm_roundtrip.bin","rb").read()[:306]
cs=Cs(CS_ARCH_X86,CS_MODE_64)
for i in cs.disasm(code,0):
    if "rbp" in i.op_str or i.mnemonic in ("call","ret","jmp"):
        print(f"{i.address:04x} {i.bytes.hex():<18} {i.mnemonic:<8} {i.op_str}")
