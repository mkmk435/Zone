import sys
import pefile

def secs(f):
    pe = pefile.PE(f)
    out = {}
    for s in pe.sections:
        out[s.Name.rstrip(b"\x00").decode()] = (s.VirtualAddress, s.Misc_VirtualSize,
                                                s.SizeOfRawData, s.PointerToRawData,
                                                s.get_data() if s.SizeOfRawData else b"")
    return pe, out

a, sa = secs(sys.argv[1])
b, sb = secs(sys.argv[2])
print("EP", hex(a.OPTIONAL_HEADER.AddressOfEntryPoint), "->", hex(b.OPTIONAL_HEADER.AddressOfEntryPoint))
print("SizeOfImage", hex(a.OPTIONAL_HEADER.SizeOfImage), "->", hex(b.OPTIONAL_HEADER.SizeOfImage))
for name in sa:
    if name not in sb:
        print(name, "missing in second")
        continue
    va1, vs1, r1, p1, d1 = sa[name]
    va2, vs2, r2, p2, d2 = sb[name]
    ndiff = sum(1 for x, y in zip(d1, d2) if x != y) + abs(len(d1) - len(d2))
    print(f"{name:8s} VA {hex(va1)}->{hex(va2)} VS {hex(vs1)}->{hex(vs2)} RAW {hex(r1)}->{hex(r2)} diffbytes {ndiff}/{len(d1)}")
