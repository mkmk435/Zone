import glob, os, re

common = {80, 443, 8080, 8443, 4444, 5555, 1234, 53, 8000, 5000, 3000, 9001, 1337, 3333, 6666, 7777}
files = sorted(glob.glob(r"original_pl/**/*.bin", recursive=True))
for path in files:
    name = os.path.basename(path)
    if "reverse" not in name:
        continue
    data = open(path, "rb").read()
    hits = []
    # x86 push imm32 (68 xx xx xx xx)
    for m in re.finditer(rb"\x68(....)", data, re.S):
        v = int.from_bytes(m.group(1), "little")
        if v in common:
            hits.append((m.start(), "push", v))
    # x86 push imm16 (66 68 xx xx)
    for m in re.finditer(rb"\x66\x68(..)", data, re.S):
        v = int.from_bytes(m.group(1), "little")
        if v in common:
            hits.append((m.start(), "push16", v))
    # x64 mov r32, imm32: 41 BA / B8-BF with imm32
    for m in re.finditer(rb"\x41[\xb8-\xbf](....)", data, re.S):
        v = int.from_bytes(m.group(1), "little")
        if v in common:
            hits.append((m.start(), "mov32", v))
    # x64 movabs imm64 low dword
    for m in re.finditer(rb"[\x48\x49][\xb8-\xbf](........)", data, re.S):
        v = int.from_bytes(m.group(1), "little")
        if (v & 0xFFFF) == 2:
            hits.append((m.start(), "movabs-sockaddr", v))
    if hits:
        print(f"{path}: " + ", ".join(f"{h[1]} 0x{h[2]:x} ({h[2]}) @0x{h[0]:x}" for h in hits))
