import struct
import sys

import pefile


def probe(path):
    pe = pefile.PE(path)
    data = open(path, "rb").read()

    def read_rva(rva, size):
        for s in pe.sections:
            if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
                off = s.PointerToRawData + (rva - s.VirtualAddress)
                return data[off:off + size]
        return None

    def u32(rva):
        b = read_rva(rva, 4)
        return None if b is None else struct.unpack("<I", b)[0]

    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3]
    stats = {"no_handler": 0, "funcinfo3": 0, "funcinfo4": 0, "scope": 0, "unknown": 0}
    kinds = {}
    for i in range(d.Size // 12):
        begin, end, unwind = struct.unpack("<III", read_rva(d.VirtualAddress + i * 12, 12))
        u = unwind & ~1
        raw = read_rva(u, 4)
        if not raw:
            continue
        vf, prolog, ncodes = raw[0], raw[1], raw[2]
        flags = vf >> 3
        if not flags & 3:
            continue
        handler_off = u + 4 + ncodes * 2
        handler_off = (handler_off + 3) & ~3
        handler = u32(handler_off)
        ptr = u32(handler_off + 4)
        kind = "unknown"
        if ptr is not None:
            v = u32(ptr)
            if v in (0x19930520, 0x19930521, 0x19930522):
                kind = {0x19930520: "funcinfo3", 0x19930521: "funcinfo4",
                        0x19930522: "funcinfo4"}[v]
            else:
                cnt = v
                ok = cnt is not None and 0 < cnt < 0x400
                if ok:
                    entry = read_rva(ptr + 4, 16)
                    if entry:
                        b, e = struct.unpack("<II", entry[:8])
                        if not (0x1000 <= b < 0x1000 + 0x18000 and 0x1000 <= e < 0x1000 + 0x18000):
                            ok = False
                    else:
                        ok = False
                kind = "scope" if ok else "unknown"
        stats[kind] = stats.get(kind, 0) + 1
        kinds.setdefault((kind, flags), []).append(hex(begin))
    print(path, stats)
    for k, v in kinds.items():
        print("   ", k, len(v), v[:6])


for p in sys.argv[1:]:
    probe(p)
