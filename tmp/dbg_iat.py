import pefile, struct
for path in ("ploader.exe", "tmp/one.exe"):
    pe = pefile.PE(path)
    data = open(path,"rb").read()
    iat = pe.OPTIONAL_HEADER.DATA_DIRECTORY[12].VirtualAddress
    size = pe.OPTIONAL_HEADER.DATA_DIRECTORY[12].Size
    off = pe.get_offset_from_rva(iat)
    vals = struct.unpack_from("<%dQ" % (size//8), data, off)
    print(path, "IAT", hex(iat), "size", hex(size), "prime 6:", [hex(v) for v in vals[:6]])
    # descrittori
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[1]
    off2 = pe.get_offset_from_rva(d.VirtualAddress)
    print("  desc:", data[off2:off2+40].hex())
    for imp in pe.DIRECTORY_ENTRY_IMPORT[:1]:
        print("  dll", imp.dll, "OriginalFirstThunk", hex(imp.struct.OriginalFirstThunk),
              "FirstThunk", hex(imp.struct.FirstThunk), "Name", hex(imp.struct.Name))
        ilt_off = pe.get_offset_from_rva(imp.struct.OriginalFirstThunk)
        print("  ILT prime 4:", [hex(x) for x in struct.unpack_from("<4Q", data, ilt_off)])
