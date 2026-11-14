"""Tests for asm_wrap: execute the original and the wrapped payload.

Every test assembles a small self-contained x86-64 program (no API calls,
volatile registers only, results written to the buffer passed in RCX), runs it
on the real CPU through a fresh RWX page, then wraps it and runs the wrapped
version the same way.  The buffers must match byte for byte.

Real execution is used instead of an emulator on purpose: it also exercises the
entry stub on the actual hardware, and every run gets a different base address
from VirtualAlloc, so position independence is checked implicitly.

Run with:  python test_asm_wrap.py
"""

import base64
import os
import subprocess
import sys
import tempfile

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from keystone import Ks, KS_ARCH_X86, KS_MODE_64

from asm_wrap import AssemblyWrapping, WrapItem, WrapError, USABLE

ks = Ks(KS_ARCH_X86, KS_MODE_64)
cs = Cs(CS_ARCH_X86, CS_MODE_64)
cs.detail = True

BASE = 0x1000          # assemble-time base, only used to resolve labels

RUNNER = r'''
import ctypes, sys

with open(sys.argv[1], "rb") as handle:
    code = handle.read()

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.VirtualAlloc.restype = ctypes.c_void_p
kernel32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                  ctypes.c_uint32, ctypes.c_uint32]
address = kernel32.VirtualAlloc(None, len(code) + 16, 0x3000, 0x40)
if not address:
    sys.exit(2)
ctypes.memmove(address, code, len(code))
buffer = (ctypes.c_ubyte * 128)()
prototype = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
prototype(address)(ctypes.cast(buffer, ctypes.c_void_p))
with open(sys.argv[2], "w") as handle:
    handle.write(",".join(str(byte) for byte in buffer))
'''

PROGRAMMES = {
    "basic": """
        mov rax, 0x1234
        mov rdx, 7
    loop_head:
        add rax, rdx
        dec rdx
        jnz loop_head
        mov qword ptr [rcx], rax
        mov r8, [rcx]
        call helper
        mov qword ptr [rcx + 8], r8
        cmp r8, 0x1234
        jl skip
        mov qword ptr [rcx + 16], 0xAAAA
    skip:
        jmp fin
        mov qword ptr [rcx + 24], 0xDEAD
    fin:
        ret
    helper:
        add r8, 3
        ret
    """,
    "data": """
        mov rax, 0x11223344
        mov qword ptr [rcx], rax
        lea r9, [rcx + 8]
        mov qword ptr [r9], rax
        mov rdx, [r9]
        add rdx, 0x1000
        mov qword ptr [rcx + 16], rdx
        mov r10, 3
    back:
        sub rdx, 0x100
        dec r10
        jnz back
        mov qword ptr [rcx + 24], rdx
        ret
    """,
    "stack": """
        mov rax, 0x99
        mov rdx, 5
    again:
        push rdx
        pop r8
        add rax, r8
        dec rdx
        jnz again
        mov qword ptr [rcx], rax
        push rax
        pop r9
        mov qword ptr [rcx + 8], r9
        ret
    """,
    "manycalls": """
        mov r10, 4
        xor r11d, r11d
    outer:
        call inner
        dec r10
        jnz outer
        mov qword ptr [rcx], r11
        ret
    inner:
        add r11, 7
        ret
    """,
    "jumps": """
        mov rax, 1
        mov rdx, 0
        mov r8, 6
    top:
        add rdx, rax
        shl rax, 1
        dec r8
        jnz top
        mov qword ptr [rcx], rdx
        cmp rdx, 63
        jne bad
        mov qword ptr [rcx + 8], 0x600D
    bad:
        ret
    """,
}


def assemble(source):
    encoding, _ = ks.asm(source, BASE)
    if not encoding:
        raise RuntimeError("keystone failed")
    return bytes(encoding)


class Runner:
    """Execute payloads in fresh child processes."""

    def __init__(self):
        self.directory = tempfile.mkdtemp(prefix="zone-wrap-test-")
        self.runner = os.path.join(self.directory, "runner.py")
        with open(self.runner, "w") as handle:
            handle.write(RUNNER)
        self.counter = 0

    def __call__(self, payload):
        """Return the 128-byte result buffer, or None if the payload crashed."""
        self.counter += 1
        code_path = os.path.join(self.directory,
                                 f"payload{self.counter}.bin")
        out_path = os.path.join(self.directory, f"out{self.counter}.txt")
        with open(code_path, "wb") as handle:
            handle.write(payload)
        result = subprocess.run(
            [sys.executable, self.runner, code_path, out_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=30)
        if result.returncode != 0 or not os.path.exists(out_path):
            return None
        with open(out_path) as handle:
            text = handle.read().strip()
        if not text:
            return None
        return bytes(int(value) for value in text.split(","))


def wrap_program(code, seed, ghost=0.2, junk=0.15):
    """Disassemble a payload, wrap it and return (wrapper, payload bytes)."""
    instructions = list(cs.disasm(code, BASE))
    covered = sum(insn.size for insn in instructions)
    assert covered == len(code), (covered, len(code))
    items = [WrapItem(key=insn.address, addr=insn.address,
                      data=bytes(insn.bytes))
             for insn in instructions]
    wrapper = AssemblyWrapping(seed=seed, ghost_probability=ghost,
                               junk_probability=junk)
    wrapper.plan(items)
    lookup = {item.key: item.data for item in items}
    payload = wrapper.render(lambda key: lookup[key])
    return wrapper, payload


def test_semantics(run):
    failures = 0
    checked = 0
    for name, source in PROGRAMMES.items():
        code = assemble(source)
        expected = run(code)
        if expected is None:
            print(f"FAIL {name}: the original payload crashed")
            failures += 1
            continue
        for seed in range(6):
            checked += 1
            wrapper, payload = wrap_program(code, seed)
            got = run(payload)
            if got is None:
                failures += 1
                print(f"FAIL {name} seed={seed}: wrapped payload crashed "
                      f"({wrapper.describe()})")
                continue
            if got != expected:
                failures += 1
                differences = [
                    f"buf+{offset:#x}: {expected[offset]:02x} -> "
                    f"{got[offset]:02x}"
                    for offset in range(len(expected))
                    if got[offset] != expected[offset]]
                print(f"FAIL {name} seed={seed}: " + "; ".join(differences[:6]))
    print(f"semantics: {checked - failures}/{checked} runs matched")
    return failures == 0


def test_hidden_from_linear_sweep():
    """A linear sweep must not land on the hidden instructions."""
    failures = 0
    checked = 0
    for name, source in PROGRAMMES.items():
        code = assemble(source)
        for seed in range(3):
            checked += 1
            wrapper, payload = wrap_program(code, seed)
            hidden = {wrapper.new_address[item.key] for item in wrapper.items
                      if not item.forced_raw and len(item.data) <= USABLE}
            sweep = {insn.address for insn in cs.disasm(payload, BASE)}
            visible = hidden & sweep
            # a hidden start can only coincide with a sweep start if the
            # sweep lost the 10-byte stride, so any overlap is a real bug
            if visible:
                failures += 1
                print(f"FAIL hidden {name} seed={seed}: {len(visible)} "
                      "instruction(s) visible to a linear sweep")
    print(f"hidden: {checked - failures}/{checked} layouts clean")
    return failures == 0


def test_encodings_are_legal():
    """Every byte of the payload must decode as some instruction."""
    failures = 0
    for name, source in PROGRAMMES.items():
        code = assemble(source)
        wrapper, payload = wrap_program(code, 1)
        offset = 0
        while offset < len(payload):
            insn = next(cs.disasm(payload[offset:], BASE + offset, count=1),
                        None)
            if insn is None:
                failures += 1
                print(f"FAIL legal {name}: no instruction at offset "
                      f"{offset:#x}")
                break
            offset += insn.size
        if offset != len(payload):
            failures += 1
            print(f"FAIL legal {name}: coverage {offset}/{len(payload)}")
    print(f"legal: {failures} failure(s)")
    return failures == 0


def test_rejects_gaps():
    items = [WrapItem(key=0, addr=0, data=b"\x90"),
             WrapItem(key=1, addr=4, data=b"\x90")]
    try:
        AssemblyWrapping(seed=0).plan(items)
    except WrapError:
        print("gaps: rejected as expected")
        return True
    print("FAIL gaps: accepted")
    return False


def test_data_fixup_items_are_opaque():
    """A getpc call rewritten to jmp by the data layer must render and verify.

    Zone replaces a 5-byte `call` with a 5-byte `jmp` to the stub inside the
    appended data blob after the wrap layout is fixed.  The wrapper must treat
    that instruction as opaque: no relocation and no mnemonic comparison.
    """
    call = b"\xE8\x00\x00\x00\x00"
    jmp = b"\xE9\x00\x00\x00\x00"
    item = WrapItem(key=0, addr=0, data=call, data_fixup=True)
    wrapper = AssemblyWrapping(seed=0)
    try:
        wrapper.plan([item])
        payload = wrapper.render(lambda _key: jmp)
    except WrapError as error:
        print(f"FAIL data_fixup: {error}")
        return False
    hidden = wrapper.new_address[0]
    if payload[hidden:hidden + 5] != jmp:
        print("FAIL data_fixup: jmp bytes were overwritten")
        return False
    print("data_fixup: opaque jmp accepted")
    return True


def main():
    run = Runner()
    ok = True
    ok &= test_semantics(run)
    ok &= test_hidden_from_linear_sweep()
    ok &= test_encodings_are_legal()
    ok &= test_rejects_gaps()
    ok &= test_data_fixup_items_are_opaque()
    print("RESULT:", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
