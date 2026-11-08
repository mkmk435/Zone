import glob, os, struct

files = sorted(glob.glob(r"original_pl/**/*.bin", recursive=True))
print(f"{'file':<60} {'LHOST':<16} {'LPORT':<10} note")
print("-" * 110)

def analyze(path):
    data = open(path, "rb").read()
    bits = 64 if "\\x64\\" in path else 32
    host = None
    port = None
    notes = []

    # Plaintext string host (DNS / HTTP stagers)
    if b"127.0.0.1" in data:
        host = "127.0.0.1"
        notes.append("stringa '127.0.0.1'")

    # x86: push imm32 family+port  -> 68 02 00 pp pp
    idx = 0
    while True:
        i = data.find(b"\x68\x02\x00", idx)
        if i < 0:
            break
        if i + 4 < len(data):
            p = int.from_bytes(data[i + 3:i + 5], "big")
            if port is None:
                port = p
        idx = i + 1

    # x86 nonx: 66 68 pp pp (push word port), preceded by push ip
    idx = 0
    while True:
        i = data.find(b"\x66\x68", idx)
        if i < 0:
            break
        if i + 4 < len(data):
            p = int.from_bytes(data[i + 2:i + 4], "big")
            if port is None and 0 < p < 65536:
                port = p
        idx = i + 1

    # x64 movabs imm64 * 02 00 pp pp ii ii ii ii
    for i in range(len(data) - 10):
        if data[i] in (0x48, 0x49) and data[i + 1] in (0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF):
            imm = int.from_bytes(data[i + 2:i + 10], "little")
            if (imm & 0xFFFF) == 2:
                p = (imm >> 16) & 0xFFFF
                if port is None:
                    port = p
                if host is None:
                    ip = struct.unpack("<I", struct.pack("<I", imm >> 32))[0]
                    host = ".".join(str(b) for b in struct.pack("<I", imm >> 32))

    # x86 IP push imm32 with 127.0.0.1
    if host is None and b"\x68\x7f\x00\x00\x01" in data:
        host = "127.0.0.1"

    if "allports" in os.path.basename(path):
        notes.append("scansiona tutte le porte partendo da %s" % port)
    if "dns" in os.path.basename(path):
        notes.append("risolve il nome via gethostbyname")
    if "nonx" in os.path.basename(path):
        notes.append("stager non-XOR")
    return host, port, ", ".join(notes)

for path in files:
    name = os.path.basename(path)
    if "reverse" not in name:
        continue
    host, port, notes = analyze(path)
    if host is None and port is None:
        continue
    print(f"{path[12:]:<60} {str(host):<16} {str(port):<10} {notes}")
