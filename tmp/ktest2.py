from keystone import *
for mode in (KS_MODE_64, KS_MODE_32):
    ks = Ks(KS_ARCH_X86, mode)
    print("MODE", mode)
    for src in [
        "db 0x90, 0x91",
        ".byte 0x90, 0x91",
        "L1:\n jmp L1",
        "mov rax, [rip + L1]\nL1:\n nop" if mode==KS_MODE_64 else "mov eax, [L1]\nL1:\n nop",
        "mov qword ptr [rip + 0x10], rax" if mode==KS_MODE_64 else "mov dword ptr [0x10], eax",
        "lea rax, [rip + L1]\nL1:\n nop" if mode==KS_MODE_64 else "lea eax, [L1]\nL1:\n nop",
    ]:
        try:
            enc, cnt = ks.asm(src, 0)
            print("OK", bytes(enc).hex(), "|", src.replace("\n","; "))
        except Exception as e:
            print("ERR", type(e).__name__, e, "|", src.replace("\n","; "))
