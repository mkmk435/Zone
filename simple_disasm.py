"""Print a linear disassembly of a raw binary or PE/ELF file.

Examples:
    python simple_disasm.py payload.bin --arch x86
    python simple_disasm.py payload.bin --arch x64 --base 0x400000
    python simple_disasm.py loader.exe --arch auto
"""

import argparse
import struct
from pathlib import Path

from capstone import (
    CS_ARCH_ARM,
    CS_ARCH_ARM64,
    CS_ARCH_MIPS,
    CS_ARCH_PPC,
    CS_ARCH_X86,
    CS_MODE_16,
    CS_MODE_32,
    CS_MODE_64,
    CS_MODE_ARM,
    CS_MODE_BIG_ENDIAN,
    CS_MODE_LITTLE_ENDIAN,
    CS_MODE_MIPS32,
    CS_MODE_MIPS64,
    CS_MODE_THUMB,
    Cs,
)

# Capstone mode combinations for the supported architecture names.
ARCHES = {
    "x86": (CS_ARCH_X86, CS_MODE_32),
    "x64": (CS_ARCH_X86, CS_MODE_64),
    "x16": (CS_ARCH_X86, CS_MODE_16),
    "arm": (CS_ARCH_ARM, CS_MODE_ARM),
    "thumb": (CS_ARCH_ARM, CS_MODE_THUMB),
    "arm64": (CS_ARCH_ARM64, CS_MODE_ARM),
    "mips": (CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_BIG_ENDIAN),
    "mipsel": (CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN),
    "mips64": (CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_BIG_ENDIAN),
    "mips64el": (CS_ARCH_MIPS, CS_MODE_MIPS64 | CS_MODE_LITTLE_ENDIAN),
    "ppc": (CS_ARCH_PPC, CS_MODE_32 | CS_MODE_BIG_ENDIAN),
    "ppc64": (CS_ARCH_PPC, CS_MODE_64 | CS_MODE_BIG_ENDIAN),
    "ppc64le": (CS_ARCH_PPC, CS_MODE_64 | CS_MODE_LITTLE_ENDIAN),
}

PE_MACHINES = {
    0x014C: "x86",
    0x8664: "x64",
    0x01C0: "arm",
    0x01C4: "thumb",
    0xAA64: "arm64",
    0x0166: "mips",
    0x01F0: "ppc",
    0x01F1: "ppc64",
}

ELF_MACHINES = {
    3: "x86",
    62: "x64",
    40: "arm",
    183: "arm64",
    8: "mips",
    10: "mips",
    20: "ppc",
    21: "ppc64",
}


def detect_arch(data: bytes) -> tuple[str | None, str]:
    """Return (architecture, reason) from a PE or ELF header."""
    if len(data) >= 0x40 and data[:2] == b"MZ":
        try:
            pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
            if (pe_offset + 0x18 <= len(data)
                    and data[pe_offset:pe_offset + 4] == b"PE\x00\x00"):
                machine = struct.unpack_from("<H", data, pe_offset + 4)[0]
                arch = PE_MACHINES.get(machine)
                return arch, f"PE machine {machine:#06x}"
        except struct.error:
            pass

    if len(data) >= 0x14 and data[:4] == b"\x7fELF":
        byte_order = {1: "<", 2: ">"}.get(data[5], "<")
        try:
            machine = struct.unpack_from(byte_order + "H", data, 0x12)[0]
            arch = ELF_MACHINES.get(machine)
            return arch, f"ELF machine {machine}"
        except struct.error:
            pass

    return None, "no PE/ELF header"


def parse_base(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "base must be decimal or 0x-prefixed hex") from exc


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", type=Path, help="binary file to disassemble")
    parser.add_argument(
        "--arch", "-a",
        choices=("auto",) + tuple(ARCHES),
        default="auto",
        help="architecture (default: auto, then x64 for raw shellcode)")
    parser.add_argument(
        "--base", "-b", type=parse_base, default=0,
        help="base address printed for offsets (default: 0)")
    args = parser.parse_args()

    try:
        data = args.file.read_bytes()
    except OSError as exc:
        parser.error(str(exc))

    if args.arch == "auto":
        arch, reason = detect_arch(data)
        if arch is None:
            arch = "x64"
            reason = f"{reason}; using x64 fallback"
        else:
            reason = f"{reason}; selected {arch}"
    else:
        arch = args.arch
        reason = "explicit --arch"

    cs_arch, cs_mode = ARCHES[arch]
    try:
        decoder = Cs(cs_arch, cs_mode)
    except Exception as exc:  # Capstone can reject an unsupported mode
        parser.error(f"cannot initialize Capstone for {arch}: {exc}")
    decoder.skipdata = True

    print(f"Architecture: {arch} (arch={cs_arch}, mode={cs_mode:#x})")
    print(f"Base: {args.base:#x}  ({reason})")
    for instruction in decoder.disasm(data, args.base):
        raw_bytes = instruction.bytes.hex(" ")
        print(f"{instruction.address:08x}  {raw_bytes:<44}  "
              f"{instruction.mnemonic:<7} {instruction.op_str}")


if __name__ == "__main__":
    main()
