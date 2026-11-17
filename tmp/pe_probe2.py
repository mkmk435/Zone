import struct
import sys

import pefile


def analyze(path):
    pe = pefile.PE(path)
    data = open(path, "rb").read()
    print("=" * 60)
    print(path, "size", hex(len(data)))
    magic = {0x19930520: "FH3", 0x19930521: "FH4", 0x19930522: "FH4+flags"}
    for m, name in magic.items():
        pat = struct.pack("<I", m)
        hits = []
        start = 0
        while True:
            i = data.find(pat, start)
            if i < 0:
                break
            hits.append(i)
            start = i + 1
        print(f"  C++ EH magic {name} (0x{m:x}): {len(hits)} hits")

    # pdata
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3]
    n = d.Size // 12
    handlers = {}
    unwind_sec = None
    for idx in range(n):
        off = pe.get_offset_from_rva(d.VirtualAddress + idx * 12)
        begin, end, unwind = struct.unpack_from("<III", data, off)
        uoff = pe.get_offset_from_rva(unwind & ~1)
        if uoff is None:
            print("   bad unwind rva", hex(unwind))
            continue
        vf = data[uoff]
        version = vf & 7
        flags = vf >> 3
        prolog = data[uoff + 1]
        codes = data[uoff + 2]
        freg = data[uoff + 3]
        key = (flags, prolog, codes)
        handlers[flags] = handlers.get(flags, 0) + 1
        if idx < 3:
            print("   RF %08x-%08x unwind=%08x version=%d flags=%d prolog=%d codes=%d freg=0x%x" %
                  (begin, end, unwind, version, flags, prolog, codes, freg))
    print("  pdata entries:", n, "flags histogram:", handlers)

    # relocs
    if hasattr(pe, "DIRECTORY_ENTRY_BASERELOC"):
        types = {}
        total = 0
        for b in pe.DIRECTORY_ENTRY_BASERELOC:
            for e in b.entries:
                types[e.type] = types.get(e.type, 0) + 1
                total += 1
        print("  relocs:", total, types)
    import collections
    il = getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])
    print("  imports:", len(il), "dlls", sum(len(i.imports) for i in il))
    print("  has TLS:", hasattr(pe, "DIRECTORY_ENTRY_TLS"),
          "has EXPORT:", hasattr(pe, "DIRECTORY_ENTRY_EXPORT"),
          "has RESOURCE:", hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"),
          "delay:", hasattr(pe, "DIRECTORY_ENTRY_DELAY_IMPORT"))


for p in sys.argv[1:]:
    analyze(p)
