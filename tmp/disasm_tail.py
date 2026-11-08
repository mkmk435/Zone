import sys, capstone

for path, arch in [
    (r"original_pl\x86\windows_shell_reverse_tcp.bin", 32),
    (r"original_pl\x64\windows_x64_shell_reverse_tcp.bin", 64),
]:
    data = open(path, "rb").read()
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32 if arch == 32 else capstone.CS_MODE_64)
    md.detail = False
    print("=" * 70)
    print(path, len(data))
    off = len(data) - 64
    for ins in md.disasm(data[off:], off):
        print(f"{ins.address:04x}: {ins.bytes.hex():<24} {ins.mnemonic} {ins.op_str}")
