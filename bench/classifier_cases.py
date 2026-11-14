"""Classifier-only fixtures with independent ground truth.

Kept separate from the 13-case functional corpus so the existing native/LLM
results stay comparable. Two kinds:
  * nodata: no inline data at all; the correct classification is the empty set;
  * multidata: two separate inline strings, two ground-truth ranges.
"""
from __future__ import annotations


def _string(text: str) -> str:
    data = text.encode("ascii") + b"\x00"
    return ".byte " + ",".join(f"0x{byte:02x}" for byte in data)


X64 = [
    {
        "name": "nodata",
        "kind": "senza_dati",
        "source": """
            mov rax, 0x1122
            add rax, 0x3344
            mov qword ptr [rcx], rax
            ret
        """,
        "expect": [{"offset": 0, "bytes": (0x4466).to_bytes(8, "little").hex()}],
        "data_text": [],
        "notes": "nessun dato inline; classificazione corretta = insieme vuoto",
    },
    {
        "name": "multidata",
        "kind": "due_intervalli",
        "source": """
            jmp start
        msg1: """ + _string("alpha") + """
        start:
            lea rsi, [rip + msg1]
            mov rdi, rcx
        c1:
            mov al, [rsi]
            mov [rdi], al
            inc rsi
            inc rdi
            test al, al
            jnz c1
            lea rsi, [rip + msg2]
            lea rdi, [rcx + 16]
        c2:
            mov al, [rsi]
            mov [rdi], al
            inc rsi
            inc rdi
            test al, al
            jnz c2
            ret
        msg2: """ + _string("beta"),
        "expect": [
            {"offset": 0, "bytes": b"alpha\x00".hex()},
            {"offset": 16, "bytes": b"beta\x00".hex()},
        ],
        "data_text": ["alpha", "beta"],
        "notes": "due stringhe inline reference separatamente",
    },
    {
        "name": "databait",
        "kind": "codice_simile_a_dati",
        "source": """
            mov rax, 0x4142434445464748
            mov qword ptr [rcx], rax
            ret
        """,
        "expect": [{"offset": 0,
                    "bytes": (0x4142434445464748).to_bytes(8, "little").hex()}],
        "data_text": [],
        "data_patterns": [],
        "notes": "immediato ASCII dentro il codice: nessun dato da estrarre",
    },
    {
        "name": "table",
        "kind": "tabella_binaria",
        "source": """
            lea rsi, [rip + table]
            mov eax, [rsi]
            add eax, [rsi + 4]
            add eax, [rsi + 8]
            add eax, [rsi + 12]
            mov [rcx], eax
            ret
        table: .byte 0x01,0,0,0, 0x02,0,0,0, 0x03,0,0,0, 0x04,0,0,0
        """,
        "expect": [{"offset": 0, "bytes": (10).to_bytes(4, "little").hex()}],
        "data_text": [],
        "data_patterns": [
            {"hex": "01000000020000000300000004000000", "name": "table16"},
        ],
        "notes": "tabella binaria di 16 byte, non ASCII",
    },
]

X86 = [
    {
        "name": "nodata",
        "kind": "senza_dati",
        "source": """
            mov ecx, [esp + 4]
            mov eax, 0x1122
            add eax, 0x3344
            mov [ecx], eax
            ret
        """,
        "expect": [{"offset": 0, "bytes": (0x4466).to_bytes(4, "little").hex()}],
        "data_text": [],
        "notes": "nessun dato inline 32-bit",
    },
    {
        "name": "multidata",
        "kind": "due_intervalli",
        "source": """
            mov edi, [esp + 4]
            call getpc1
        msg1: """ + _string("alpha") + """
        getpc1:
            pop esi
        c1:
            mov al, [esi]
            mov [edi], al
            inc esi
            inc edi
            test al, al
            jnz c1
            mov edi, [esp + 4]
            add edi, 16
            call getpc2
        msg2: """ + _string("beta") + """
        getpc2:
            pop esi
        c2:
            mov al, [esi]
            mov [edi], al
            inc esi
            inc edi
            test al, al
            jnz c2
            ret
        """,
        "expect": [
            {"offset": 0, "bytes": b"alpha\x00".hex()},
            {"offset": 16, "bytes": b"beta\x00".hex()},
        ],
        "data_text": ["alpha", "beta"],
        "notes": "due blocchi call/pop con due stringhe 32-bit",
    },
]

CASES = {"x64": X64, "x86": X86}
