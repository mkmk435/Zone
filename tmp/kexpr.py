from keystone import *
ks=Ks(KS_ARCH_X86,KS_MODE_64)
for src in [
 "lea rcx, [rip + DATA_0 + 4]\nDATA_0:\n .byte 0x90,0x90,0x90,0x90,0x90",
 "mov eax, DATA_0 + 4\nDATA_0:\n .byte 0x90",
 "mov eax, [DATA_0 + 4]\nDATA_0:\n .byte 0x90,0x90,0x90,0x90,0x90",
 "global _start\n_start:\n nop",
]:
    try:
        e,_=ks.asm(src,0); print("OK",bytes(e).hex(),"|",src.replace("\n","; "))
    except Exception as ex: print("ERR",ex,"|",src.replace("\n","; "))
