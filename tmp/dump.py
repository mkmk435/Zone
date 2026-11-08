import capstone, sys

def dump(path, bits):
    data = open(path, "rb").read()
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32 if bits == 32 else capstone.CS_MODE_64)
    print("=" * 78)
    print(path, len(data))
    for ins in md.disasm(data, 0):
        print(f"{ins.address:04x}: {ins.bytes.hex():<26} {ins.mnemonic} {ins.op_str}")

dump(sys.argv[1], int(sys.argv[2]))
