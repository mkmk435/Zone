from capstone import *
for name,n in (("tmp/native_combo.bin",326),("tmp/native_xd_eq.bin",326)):
    raw=open(name,"rb").read()
    cs=Cs(CS_ARCH_X86,CS_MODE_64)
    print("====",name,len(raw))
    for i in cs.disasm(raw[:n],0):
        if i.address < 0x50 or 0xd0 <= i.address <= 0xf0:
            print(f"{i.address:04x} {i.bytes.hex():<18} {i.mnemonic:<8} {i.op_str}")
