from capstone import *
for name,n in (("tmp/llm_roundtrip.bin",306),("tmp/llm_mock_nop.bin",323)):
    code=open(name,"rb").read()[:n]
    cs=Cs(CS_ARCH_X86,CS_MODE_64)
    print("====",name)
    for i in cs.disasm(code,0):
        if 0x28 <= i.address <= 0x48:
            print(f"{i.address:04x} {i.bytes.hex():<18} {i.mnemonic:<8} {i.op_str}")
