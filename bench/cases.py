"""Benign fixture corpus for the Zone benchmark.

Every case declares, before any test:
  * the assembly source assembled at base 0;
  * the bytes the payload must write into the 256-byte result buffer;
  * whether the case contains inline data and therefore needs `-xd`.
The runner passes the buffer pointer in RCX (x64) or [esp+4] (x86 cdecl);
bytes not listed in `expect` must stay 0xCC.

Expected values are computed from the constants below (not from a mutant) and
are validated against the original payload by bench/build_fixtures.py.
"""
from __future__ import annotations


def _string(text: str) -> str:
    data = text.encode("ascii") + b"\x00"
    return ".byte " + ",".join(f"0x{byte:02x}" for byte in data)


def _str_expect(text: str):
    data = text.encode("ascii") + b"\x00"
    return [{"offset": 0, "bytes": data.hex()}]


# (0x12345678 + 0x1111 - 0x2222) * 3
ARITH64 = (0x12345678 + 0x1111 - 0x2222) * 3
ARITH32 = ARITH64 & 0xFFFFFFFF

X64 = [
    {
        "name": "arith",
        "kind": "calcolo",
        "source": """
            mov rax, 0x12345678
            add rax, 0x1111
            sub rax, 0x2222
            imul rax, rax, 3
            mov qword ptr [rcx], rax
            xor r8, r8
            mov r9, 5
        loop1:
            add r8, r9
            dec r9
            jnz loop1
            mov qword ptr [rcx + 8], r8
            ret
        """,
        "expect": [
            {"offset": 0, "bytes": ARITH64.to_bytes(8, "little").hex()},
            {"offset": 8, "bytes": (15).to_bytes(8, "little").hex()},
        ],
        "requires_extract": False,
        "notes": "aritmetica + piccolo ciclo",
    },
    {
        "name": "branch",
        "kind": "diramazioni",
        "source": """
            mov rax, 7
            cmp rax, 7
            jne bad
            mov qword ptr [rcx], 0xAAAA
            jmp done
        bad:
            mov qword ptr [rcx], 0xDEAD
        done:
            mov rdx, 0
            mov r8, 10
            cmp r8, 10
            jg big
            mov qword ptr [rcx + 8], 0x1111
            jmp fin
        big:
            mov qword ptr [rcx + 8], 0x2222
        fin:
            ret
        """,
        "expect": [
            {"offset": 0, "bytes": (0xAAAA).to_bytes(8, "little").hex()},
            {"offset": 8, "bytes": (0x1111).to_bytes(8, "little").hex()},
        ],
        "requires_extract": False,
        "notes": "if/else con due condizioni",
    },
    {
        "name": "loop",
        "kind": "cicli",
        "source": """
            xor rax, rax
            mov rdx, 100
        sum:
            add rax, rdx
            dec rdx
            jnz sum
            mov qword ptr [rcx], rax
            ret
        """,
        "expect": [
            {"offset": 0, "bytes": (5050).to_bytes(8, "little").hex()},
        ],
        "requires_extract": False,
        "notes": "somma 1..100",
    },
    {
        "name": "call",
        "kind": "chiamate_locali",
        "source": """
            mov r10, 4
            xor r11, r11
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
        "expect": [
            {"offset": 0, "bytes": (28).to_bytes(8, "little").hex()},
        ],
        "requires_extract": False,
        "notes": "subroutine locale chiamata 4 volte",
    },
    {
        "name": "mixed",
        "kind": "misto",
        "source": """
            xor rax, rax
            mov rdx, 6
        top:
            add rax, rdx
            dec rdx
            jnz top
            cmp rax, 21
            jne bad
            call helper
            mov qword ptr [rcx], rax
            jmp fin
        bad:
            mov qword ptr [rcx], 0xBAD
        fin:
            ret
        helper:
            add rax, 100
            ret
        """,
        "expect": [
            {"offset": 0, "bytes": (121).to_bytes(8, "little").hex()},
        ],
        "requires_extract": False,
        "notes": "ciclo + branch + call locale",
    },
    {
        "name": "strings",
        "kind": "stringhe_dati_inline",
        "source": """
            lea rsi, [rip + msg]
            mov rdi, rcx
        copy:
            mov al, [rsi]
            mov [rdi], al
            inc rsi
            inc rdi
            test al, al
            jnz copy
            ret
        msg: """ + _string("Hello, Zone!"),
        "expect": _str_expect("Hello, Zone!"),
        "requires_extract": True,
        "data_text": "Hello, Zone!",
        "notes": "stringa inline con riferimento RIP-relative",
    },
    {
        "name": "getpc",
        "kind": "dati_inline_getpc",
        "source": """
            call getpc
        msg: """ + _string("getpc data!") + """
        getpc:
            pop rsi
            mov rdi, rcx
        copy:
            mov al, [rsi]
            mov [rdi], al
            inc rsi
            inc rdi
            test al, al
            jnz copy
            ret
        """,
        "expect": _str_expect("getpc data!"),
        "requires_extract": True,
        "data_text": "getpc data!",
        "notes": "call $+5 / pop, dati spostati da -xd",
    },
]

X86 = [
    {
        "name": "arith",
        "kind": "calcolo",
        "source": """
            mov ecx, [esp + 4]
            mov eax, 0x12345678
            add eax, 0x1111
            sub eax, 0x2222
            imul eax, eax, 3
            mov [ecx], eax
            xor eax, eax
            mov edx, 5
        loop1:
            add eax, edx
            dec edx
            jnz loop1
            mov [ecx + 4], eax
            ret
        """,
        "expect": [
            {"offset": 0, "bytes": ARITH32.to_bytes(4, "little").hex()},
            {"offset": 4, "bytes": (15).to_bytes(4, "little").hex()},
        ],
        "requires_extract": False,
        "notes": "aritmetica 32-bit + ciclo",
    },
    {
        "name": "branch",
        "kind": "diramazioni",
        "source": """
            mov ecx, [esp + 4]
            mov eax, 7
            cmp eax, 7
            jne bad
            mov dword ptr [ecx], 0xAAAA
            jmp done
        bad:
            mov dword ptr [ecx], 0xDEAD
        done:
            mov eax, 10
            cmp eax, 10
            jg big
            mov dword ptr [ecx + 4], 0x1111
            jmp fin
        big:
            mov dword ptr [ecx + 4], 0x2222
        fin:
            ret
        """,
        "expect": [
            {"offset": 0, "bytes": (0xAAAA).to_bytes(4, "little").hex()},
            {"offset": 4, "bytes": (0x1111).to_bytes(4, "little").hex()},
        ],
        "requires_extract": False,
        "notes": "if/else 32-bit",
    },
    {
        "name": "loop",
        "kind": "cicli",
        "source": """
            mov ecx, [esp + 4]
            xor eax, eax
            mov edx, 100
        sum:
            add eax, edx
            dec edx
            jnz sum
            mov [ecx], eax
            ret
        """,
        "expect": [
            {"offset": 0, "bytes": (5050).to_bytes(4, "little").hex()},
        ],
        "requires_extract": False,
        "notes": "somma 1..100 32-bit",
    },
    {
        "name": "call",
        "kind": "chiamate_locali",
        "source": """
            mov ecx, [esp + 4]
            xor eax, eax
            mov edx, 4
        outer:
            call inner
            dec edx
            jnz outer
            mov [ecx], eax
            ret
        inner:
            add eax, 7
            ret
        """,
        "expect": [
            {"offset": 0, "bytes": (28).to_bytes(4, "little").hex()},
        ],
        "requires_extract": False,
        "notes": "subroutine locale 32-bit",
    },
    {
        "name": "strings",
        "kind": "stringhe_dati_inline",
        "source": """
            mov edi, [esp + 4]
            call getpc
        msg: """ + _string("Hello, x86!") + """
        getpc:
            pop esi
        copy:
            mov al, [esi]
            mov [edi], al
            inc esi
            inc edi
            test al, al
            jnz copy
            ret
        """,
        "expect": _str_expect("Hello, x86!"),
        "requires_extract": True,
        "data_text": "Hello, x86!",
        "notes": "call/pop + stringa inline 32-bit",
    },
    {
        "name": "mixed",
        "kind": "misto",
        "source": """
            mov ecx, [esp + 4]
            xor eax, eax
            mov edx, 6
        top:
            add eax, edx
            dec edx
            jnz top
            cmp eax, 21
            jne bad
            call helper
            mov [ecx], eax
            jmp fin
        bad:
            mov dword ptr [ecx], 0xBAD
        fin:
            ret
        helper:
            add eax, 100
            ret
        """,
        "expect": [
            {"offset": 0, "bytes": (121).to_bytes(4, "little").hex()},
        ],
        "requires_extract": False,
        "notes": "ciclo + branch + call 32-bit",
    },
]

CASES = {"x64": X64, "x86": X86}
