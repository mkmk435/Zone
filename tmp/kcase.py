from keystone import *
ks=Ks(KS_ARCH_X86,KS_MODE_64)
for src in ["L_A: nop\njmp L_A", "L_A: nop\njmp l_a"]:
    try:
        e,_=ks.asm(src,0); print("OK",bytes(e).hex(),repr(src))
    except Exception as ex: print("ERR",ex,repr(src))
