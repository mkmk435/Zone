"""Genera un PE x64 minimale (senza import, senza .pdata) per testare i passi.

Il codice calcola 42 in eax e fa `ret`: l'exit code del processo e' 42, cosi'
si verifica la semantica dopo l'obfuscazione senza usare payload.

Uso: python tmp/make_test_pe.py out.exe
"""
import struct
import sys

from keystone import KS_ARCH_X86, KS_MODE_64, Ks

IMAGE_BASE = 0x140000000
SECTION_ALIGN = 0x1000
FILE_ALIGN = 0x200
TEXT_VA = 0x1000
RDATA_VA = 0x2000
DATA_VALUE = 0x12345678

SOURCE = """
    mov eax, 0
    mov ecx, 5
loop1:
    add eax, 3
    loop loop1
    jrcxz skip
    add eax, 100
skip:
    call sub1
    jmp done
sub1:
    add eax, 27
    ret
done:
    mov edx, dword ptr [rip + 0]
    cmp edx, 0x12345678
    je  ok
    mov eax, 7
ok:
    ret
"""


def build(path):
    ks = Ks(KS_ARCH_X86, KS_MODE_64)
    code, _ = ks.asm(SOURCE, TEXT_VA)
    code = bytearray(code)
    # sistema il displacement della lettura RIP-relative verso .rdata
    from capstone import CS_ARCH_X86, CS_MODE_64, Cs
    cs = Cs(CS_ARCH_X86, CS_MODE_64)
    cs.detail = True
    patched = False
    for insn in cs.disasm(bytes(code), TEXT_VA):
        if insn.mnemonic == "mov" and "rip" in insn.op_str and "edx" in insn.op_str:
            disp = RDATA_VA - (insn.address + insn.size)
            field = (insn.address - TEXT_VA) + insn.encoding.disp_offset
            struct.pack_into("<i", code, field, disp)
            patched = True
    if not patched:
        print("nessun riferimento RIP da sistemare (codice minimale)")
    code = bytes(code)
    rdata = struct.pack("<I", DATA_VALUE)

    text_raw = (len(code) + FILE_ALIGN - 1) // FILE_ALIGN * FILE_ALIGN
    rdata_raw = (len(rdata) + FILE_ALIGN - 1) // FILE_ALIGN * FILE_ALIGN

    headers_size = FILE_ALIGN
    text_off = headers_size
    rdata_off = text_off + text_raw
    size_of_image = SECTION_ALIGN + SECTION_ALIGN   # .text a 0x1000, .rdata 0x2000
    size_of_image += SECTION_ALIGN

    dos = bytearray(0x80)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x80)

    pe = bytearray()
    pe += b"PE\x00\x00"
    # COFF header
    pe += struct.pack("<HHIIIHH", 0x8664, 2, 0, 0, 0, 240, 0x0022)
    # optional header (PE32+)
    optional = bytearray(240)
    struct.pack_into("<H", optional, 0, 0x20B)
    struct.pack_into("<B", optional, 2, 14)          # linker version
    struct.pack_into("<I", optional, 4, text_raw)    # SizeOfCode
    struct.pack_into("<I", optional, 8, rdata_raw)   # SizeOfInitializedData
    struct.pack_into("<I", optional, 16, TEXT_VA)    # AddressOfEntryPoint
    struct.pack_into("<I", optional, 20, TEXT_VA)    # BaseOfCode
    struct.pack_into("<Q", optional, 24, IMAGE_BASE)
    struct.pack_into("<I", optional, 32, SECTION_ALIGN)
    struct.pack_into("<I", optional, 36, FILE_ALIGN)
    struct.pack_into("<H", optional, 40, 6)          # MajorOperatingSystemVersion
    struct.pack_into("<H", optional, 48, 6)          # MajorSubsystemVersion
    struct.pack_into("<I", optional, 56, size_of_image)
    struct.pack_into("<I", optional, 60, headers_size)
    struct.pack_into("<H", optional, 68, 3)          # Subsystem: console
    struct.pack_into("<H", optional, 70, 0)          # DllCharacteristics: no ASLR/CFG
    struct.pack_into("<Q", optional, 72, 0x100000)   # SizeOfStackReserve
    struct.pack_into("<Q", optional, 80, 0x1000)     # SizeOfStackCommit
    struct.pack_into("<Q", optional, 88, 0x100000)   # SizeOfHeapReserve
    struct.pack_into("<Q", optional, 96, 0x1000)     # SizeOfHeapCommit
    struct.pack_into("<I", optional, 108, 16)        # NumberOfRvaAndSizes
    pe += optional

    def section(name, vsize, va, raw_size, raw_ptr, characteristics):
        entry = bytearray(40)
        entry[0:len(name)] = name
        struct.pack_into("<I", entry, 8, vsize)
        struct.pack_into("<I", entry, 12, va)
        struct.pack_into("<I", entry, 16, raw_size)
        struct.pack_into("<I", entry, 20, raw_ptr)
        struct.pack_into("<I", entry, 36, characteristics)
        return bytes(entry)

    pe += section(b".text\x00\x00\x00", len(code), TEXT_VA, text_raw, text_off,
                  0x60000020)
    pe += section(b".rdata\x00\x00", len(rdata), RDATA_VA, rdata_raw, rdata_off,
                  0x40000040)

    image = bytearray()
    image += dos
    image += pe
    image += b"\x00" * (headers_size - len(image))
    image += code + b"\x90" * (text_raw - len(code))
    image += rdata + b"\x00" * (rdata_raw - len(rdata))

    with open(path, "wb") as handle:
        handle.write(image)
    print("scritto %s (%d byte, .text %d byte, EP %#x)" % (path, len(image), len(code), TEXT_VA))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "tmp/test_pe.exe")
