import glob, os, struct, capstone

files = sorted(glob.glob(r"original_pl/**/*.bin", recursive=True))

for path in files:
    if "reverse" not in os.path.basename(path) and "pingback" not in os.path.basename(path):
        continue
    data = open(path, "rb").read()
    bits = 64 if "x64" in path else 32
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64 if bits == 64 else capstone.CS_MODE_32)
    insns = list(md.disasm(data, 0))
    hits = []
    for i, ins in enumerate(insns):
        if ins.mnemonic == "push" and ins.op_str.startswith("0x"):
            v = int(ins.op_str, 16) & 0xFFFFFFFF
            if (v & 0xFFFF) == 0x0002 and v != 2:
                port = (v >> 16) & 0xFFFF
                # look back for IP push
                ip = None
                for j in range(i - 1, max(-1, i - 6), -1):
                    p = insns[j]
                    if p.mnemonic == "push" and p.op_str.startswith("0x"):
                        pv = int(p.op_str, 16) & 0xFFFFFFFF
                        ip = ".".join(str(b) for b in struct.pack("<I", pv))
                        break
                hits.append((ins.address, ip, port))
        if ins.mnemonic == "movabs" and ins.op_str.startswith("r"):
            try:
                v = int(ins.op_str.split(",")[1].strip(), 16) & 0xFFFFFFFFFFFFFFFF
            except Exception:
                continue
            if (v & 0xFFFF) == 0x0002 and v != 2:
                port = (v >> 16) & 0xFFFF
                ip = ".".join(str(b) for b in struct.pack("<I", v >> 32))
                hits.append((ins.address, ip, port))
    if hits:
        print(f"{path}: {hits}")
