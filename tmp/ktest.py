from keystone import *
for mode in (KS_MODE_64, KS_MODE_32):
    print("MODE", mode)
    ks = Ks(KS_ARCH_X86, mode)
    for src in [
        "start:\n call getpc\ngetpc:\n pop %s\n add %s, blob - getpc\n jmp blob\nblob:" % (("rsi","rsi") if mode==KS_MODE_64 else ("esi","esi")),
        ("lea rsi, [rip + blob]\njmp blob\nblob:" if mode==KS_MODE_64 else "call getpc\ngetpc: pop esi\nlea esi, [blob]\njmp blob\nblob:"),
        "start:\n jmp blob\n nop\nblob:",
    ]:
        try:
            enc, cnt = ks.asm(src, 0)
            print("OK", cnt, bytes(enc).hex(), "|", src.replace("\n","; "))
        except Exception as e:
            print("ERR", type(e).__name__, e, "|", src.replace("\n","; "))
