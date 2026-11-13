from capstone import *
p = "original_pl/x64/windows_x64_messagebox.bin"
code = open(p,"rb").read()
cs = Cs(CS_ARCH_X86, CS_MODE_64); cs.detail=True
insns = list(cs.disasm(code,0))
prev=0
for i in insns:
    if i.address != prev:
        gap=code[prev:i.address]
        print(f"--- GAP {prev:04x}..{i.address:04x}: {gap!r}")
    print(f"{i.address:04x} {i.bytes.hex():<20} {i.mnemonic:<8} {i.op_str}")
    prev=i.address+i.size
if prev<len(code):
    print(f"--- TAIL {prev:04x}..{len(code):04x}: {code[prev:]!r}")
