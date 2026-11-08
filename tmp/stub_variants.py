base = bytearray(open(r"C:\Users\ubu\Desktop\Zone\tmp\x86_mb_stubonly.bin", "rb").read())

for name, start, end in (("nop_dll", 0x9B, 0xA6), ("nop_msg", 0xC4, 0xD5)):
    data = bytearray(base)
    for i in range(start, end):
        data[i] = 0x90
    path = rf"C:\Users\ubu\Desktop\Zone\tmp\x86_mb_{name}.bin"
    open(path, "wb").write(bytes(data))
    print(name, "->", path)
