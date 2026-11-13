from capstone import *
for name in ("tmp/llm_roundtrip.bin","tmp/llm_mock_nop.bin"):
    code=open(name,"rb").read()
    # find code length: data starts at first data label; for mock, 323; for roundtrip 306
    n = 323 if "mock" in name else 306
    cs=Cs(CS_ARCH_X86,CS_MODE_64); cs.detail=True
    print("====",name,"code",n)
    for i in cs.disasm(code[:n],0):
        if i.address < 0x30 or 0xd0 <= i.address <= 0xe8:
            print(f"{i.address:04x} {i.bytes.hex():<18} {i.mnemonic:<8} {i.op_str}")
