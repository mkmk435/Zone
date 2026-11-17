import pefile, struct
pe = pefile.PE("ploader.exe"); data=open("ploader.exe","rb").read()
base = pe.OPTIONAL_HEADER.ImageBase
target = 0xed71
p4 = struct.pack("<I", target)
p8 = struct.pack("<Q", base+target)
for name, pat in (("rva", p4), ("va", p8)):
    hits=[]; s=0
    while True:
        i=data.find(pat,s)
        if i<0: break
        hits.append(i); s=i+1
    print(name, len(hits), [hex(h) for h in hits[:10]])
    for h in hits[:6]:
        for sec in pe.sections:
            if sec.PointerToRawData <= h < sec.PointerToRawData+sec.SizeOfRawData:
                print("   in", sec.Name.rstrip(b"\x00").decode(), "rva", hex(sec.VirtualAddress + h - sec.PointerToRawData))
