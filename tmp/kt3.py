from keystone import *
ks=Ks(KS_ARCH_X86,KS_MODE_64)
tests = [
 "mov r9, 0",
 "mov r10d, 0x726774c",
 "call L_d9  ; GETPC: x",
 "L_d9: nop",
 "lea rdx, [rip + DATA_1]\nDATA_1:\n .byte 0x90",
 "_start:\n call L_d9  ; GETPC: x\nL_d9:\n pop rbp",
]
for t in tests:
    try:
        e,_=ks.asm(t,0); print("OK", t[:40].replace("\n","; "), bytes(e).hex())
    except Exception as ex:
        print("ERR", repr(t), ex)
