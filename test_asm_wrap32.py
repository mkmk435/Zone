"""x86 tests for asm_wrap: execute the wrapped payload with ploader86.exe.

There is no 32-bit emulator available in this environment, so the programs
carry their own oracle: they compute a value, compare it with the expected
constant and jump to a deliberate null write on mismatch.  A correct payload
returns to the loader (exit code 0); a broken one crashes (non-zero).

Run with:  python test_asm_wrap32.py
"""

import os
import subprocess
import sys
import tempfile

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from keystone import Ks, KS_ARCH_X86, KS_MODE_32

from asm_wrap import AssemblyWrapping, WrapItem, ARCH_32

ks = Ks(KS_ARCH_X86, KS_MODE_32)
cs = Cs(CS_ARCH_X86, CS_MODE_32)
cs.detail = True

LOADER = os.path.abspath("ploader86.exe")

PROGRAMMES = {
    "basic": """
        mov eax, 0x1234
        mov ecx, 7
    loop1:
        add eax, ecx
        dec ecx
        jnz loop1
        cmp eax, 0x1250
        jne fail
        mov edx, 3
        call helper
        add eax, edx
        cmp eax, 0x1255
        jne fail
        ret
    helper:
        add edx, 2
        ret
    fail:
        mov dword ptr [0], 0
    """,
    "stack": """
        mov ecx, 5
        xor eax, eax
    again:
        push ecx
        pop edx
        add eax, edx
        dec ecx
        jnz again
        cmp eax, 15
        jne fail
        ret
    fail:
        mov dword ptr [0], 0
    """,
    "data": """
        push 0x11223344
        mov eax, [esp]
        add esp, 4
        cmp eax, 0x11223344
        jne fail
        mov dword ptr [esp - 4], 0x55667788
        mov edx, [esp - 4]
        sub esp, 4
        cmp edx, 0x55667788
        jne fail
        add esp, 4
        ret
    fail:
        mov dword ptr [0], 0
    """,
    "loop": """
        xor eax, eax
        mov ecx, 10
    top:
        add eax, ecx
        loop top
        cmp eax, 55
        jne fail
        ret
    fail:
        mov dword ptr [0], 0
    """,
    "manycalls": """
        xor edx, edx
        mov ecx, 4
    outer:
        call inner
        dec ecx
        jnz outer
        cmp edx, 16
        jne fail
        ret
    inner:
        add edx, 4
        ret
    fail:
        mov dword ptr [0], 0
    """,
}


def assemble(source):
    encoding, _ = ks.asm(source, 0)
    if not encoding:
        raise RuntimeError("keystone failed")
    return bytes(encoding)


class Runner:
    def __init__(self):
        self.directory = tempfile.mkdtemp(prefix="zone-wrap32-")
        self.counter = 0

    def __call__(self, payload):
        """True when the payload returned to the loader without crashing."""
        self.counter += 1
        path = os.path.join(self.directory, f"p{self.counter}.bin")
        with open(path, "wb") as handle:
            handle.write(payload)
        try:
            result = subprocess.run([LOADER, path], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=10)
        except subprocess.TimeoutExpired:
            # a broken relocation can loop forever; treat it as a failure
            return False
        return result.returncode == 0


def wrap_program(code, seed):
    instructions = list(cs.disasm(code, 0))
    covered = sum(insn.size for insn in instructions)
    assert covered == len(code), (covered, len(code))
    items = [WrapItem(key=insn.address, addr=insn.address,
                      data=bytes(insn.bytes))
             for insn in instructions]
    wrapper = AssemblyWrapping(seed=seed, bits=32)
    wrapper.plan(items)
    lookup = {item.key: item.data for item in items}
    return wrapper, wrapper.render(lambda key: lookup[key])


def test_semantics(run):
    failures = 0
    checked = 0
    for name, source in PROGRAMMES.items():
        code = assemble(source)
        if not run(code):
            print(f"FAIL {name}: the original payload crashed")
            failures += 1
            continue
        for seed in range(8):
            checked += 1
            wrapper, payload = wrap_program(code, seed)
            if not run(payload):
                failures += 1
                print(f"FAIL {name} seed={seed}: wrapped payload crashed "
                      f"({wrapper.describe()})")
    print(f"x86 semantics: {checked - failures}/{checked} runs passed")
    return failures == 0


def test_detects_failure(run):
    """The oracle itself must notice a wrong result."""
    broken = assemble("""
        mov eax, 1
        cmp eax, 2
        jne fail
        ret
    fail:
        mov dword ptr [0], 0
    """)
    if run(broken):
        print("FAIL oracle: a wrong result was not detected")
        return False
    print("oracle: wrong result detected")
    return True


def test_capacity():
    if ARCH_32.capacity != 4 or ARCH_32.container_size != 7:
        print("FAIL capacity: unexpected 32-bit container geometry")
        return False
    print("capacity: 4 bytes per container, 7-byte container")
    return True


def test_rejects_gaps():
    try:
        AssemblyWrapping(seed=0, bits=32).plan(
            [WrapItem(key=0, addr=0, data=b"\x90"),
             WrapItem(key=1, addr=4, data=b"\x90")])
    except Exception:
        print("gaps: rejected as expected")
        return True
    print("FAIL gaps: accepted")
    return False


def main():
    run = Runner()
    ok = True
    ok &= test_semantics(run)
    ok &= test_detects_failure(run)
    ok &= test_capacity()
    ok &= test_rejects_gaps()
    print("RESULT:", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
