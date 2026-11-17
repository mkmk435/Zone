import pefile, struct
def text_off(pe, rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
for path in ("ploader.exe", "tmp/one.exe"):
    pe = pefile.PE(path); data = open(path,"rb").read()
    print(path)
    for va in (0xed6b, 0xed71, 0xed77, 0xed7d):
        off = text_off(pe, va)
        b = data[off:off+8]
        print("   %#x %s" % (va, b.hex()))
    # thunk originali: cerca FF 25 nel range
    n = 0
    rva = 0xed00
    while rva < 0xee00:
        off = text_off(pe, rva)
        if data[off] == 0xff and data[off+1] == 0x25:
            disp = struct.unpack_from("<i", data, off+2)[0]
            print("   thunk a %#x -> %#x" % (rva, rva+6+disp))
            n += 1
        rva += 1
