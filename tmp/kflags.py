from keystone import *
for mode in (KS_MODE_64, KS_MODE_32):
    ks=Ks(KS_ARCH_X86,mode)
    for src in ["pushf","pushfq","pushfd","popf","popfq","popfd","pushal","popal","pushad","popad","lodsb al, byte ptr [rsi]" if mode==KS_MODE_64 else "lodsb al, byte ptr [esi]"]:
        try:
            e,_=ks.asm(src,0); print(mode, src, "->", bytes(e).hex())
        except Exception as ex: print(mode, src, "ERR", ex)
