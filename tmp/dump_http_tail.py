import capstone
path = r"original_pl\x86\windows_custom_reverse_http.bin"
data = open(path, "rb").read()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for ins in md.disasm(data[0x1d0:], 0x1d0):
    print(f"{ins.address:04x}: {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}")
print("---- raw 0x1e0..0x220")
print(" ".join(f"{b:02x}" for b in data[0x1e0:0x220]))
print(repr(data[0x1e0:0x230]))
