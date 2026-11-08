import capstone
d = open(r"original_pl/x86/windows_custom_reverse_http.bin", "rb").read()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
print(len(d))
for ins in md.disasm(d[0x175:0x1d5], 0x175):
    print(f"{ins.address:04x}: {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}")
