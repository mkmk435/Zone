import sys
import pefile

DIRS = {
    0: "EXPORT", 1: "IMPORT", 2: "RESOURCE", 3: "EXCEPTION", 4: "SECURITY",
    5: "BASERELOC", 6: "DEBUG", 7: "ARCHITECTURE", 8: "GLOBALPTR", 9: "TLS",
    10: "LOAD_CONFIG", 11: "BOUND_IMPORT", 12: "IAT", 13: "DELAY_IMPORT",
    14: "COM_DESCRIPTOR", 15: "RESERVED",
}

for f in sys.argv[1:]:
    try:
        pe = pefile.PE(f)
    except Exception as e:
        print(f, "NOT A PE:", e)
        continue
    print("=" * 70)
    print(f, "ImageBase", hex(pe.OPTIONAL_HEADER.ImageBase),
          "EP", hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),
          "SizeOfImage", hex(pe.OPTIONAL_HEADER.SizeOfImage),
          "BaseOfCode", hex(pe.OPTIONAL_HEADER.BaseOfCode),
          "file size", hex(len(open(f, 'rb').read())))
    for s in pe.sections:
        print("   %-8s VA %-8s VSize %-8s Raw %-8s PR %-8s chars %s" % (
            s.Name.rstrip(b"\x00").decode(errors="replace"),
            hex(s.VirtualAddress), hex(s.Misc_VirtualSize),
            hex(s.SizeOfRawData), hex(s.PointerToRawData), hex(s.Characteristics)))
    for i, d in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY):
        if d.VirtualAddress:
            print("   dir %-12s VA %-8s size %s" % (DIRS.get(i, i), hex(d.VirtualAddress), hex(d.Size)))
    if hasattr(pe, "DIRECTORY_ENTRY_EXCEPTION"):
        print("   *.pdata entries:", len(pe.DIRECTORY_ENTRY_EXCEPTION))
    if hasattr(pe, "DIRECTORY_ENTRY_LOAD_CONFIG"):
        lc = pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
        print("   LoadConfig size:", hex(lc.Size), "SEH", lc.SEHandlerTable, "GuardCF", hex(getattr(lc, "GuardCFFunctionTable", 0) or 0))
