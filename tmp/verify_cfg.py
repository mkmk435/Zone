import glob, os

files = sorted(glob.glob(r"original_pl/**/*.bin", recursive=True))
ok, bad = [], []
for path in files:
    name = os.path.basename(path)
    if "reverse" not in name:
        continue
    d = open(path, "rb").read()
    bits = 64 if "\\x64\\" in path else 32
    is_tcp = "tcp" in name
    is_http = ("http" in name)

    if bits == 64 and is_tcp:
        good = d.find(bytes.fromhex("49bc020004d27f000001")) >= 0 or d.find(bytes.fromhex("49bc020004d2")) >= 0
        # generic: any movabs imm64 with sockaddr 127.0.0.1:1234
        good = bytes.fromhex("020004d27f000001") in d
    elif bits == 32 and is_tcp and "nonx" in name:
        good = bytes.fromhex("687f000001666804d26653") in d
    elif bits == 32 and is_tcp:
        good = bytes.fromhex("687f000001") in d and bytes.fromhex("68020004d2") in d
    elif is_http:
        # host string + port 1234 constant (x86 push 0x4d2 / x64 mov r8,0x4d2) or UTF-16 URL
        port_ok = bytes.fromhex("d2040000") in d or bytes.fromhex("04d2") in d
        host_ok = b"127.0.0.1" in d or "127.0.0.1".encode("utf-16-le") in d
        good = port_ok and host_ok
    else:
        good = False

    (ok if good else bad).append(path)

print("OK:", len(ok))
for p in ok:
    print("  ", p[12:])
print("NOT MATCHED:", len(bad))
for p in bad:
    print("  ", p[12:])
