import pefile, struct
pe = pefile.PE("ploader.exe")
imp = pe.DIRECTORY_ENTRY_IMPORT[0]
d = imp.struct.dump_dict()
print("desc fields:", {k: (v.get("Value"), v.get("FileOffset")) for k, v in d.items() if isinstance(v, dict) and "FileOffset" in v})
print("dir IMPORT va", hex(pe.OPTIONAL_HEADER.DATA_DIRECTORY[1].VirtualAddress))
print("pefile get_offset_from_rva(dir):", hex(pe.get_offset_from_rva(pe.OPTIONAL_HEADER.DATA_DIRECTORY[1].VirtualAddress)))
data = open("ploader.exe","rb").read()
off = pe.get_offset_from_rva(pe.OPTIONAL_HEADER.DATA_DIRECTORY[1].VirtualAddress)
print("primi 20 byte del descrittore:", data[off:off+20].hex())
