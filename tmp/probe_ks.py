from keystone import *
ks = Ks(KS_ARCH_X86, KS_MODE_64)
tests = {
 "labels": "start:\n mov eax,0\n mov ecx,5\nloop1:\n add eax,3\n loop loop1\n jrcxz skip\n add eax,100\nskip:\n call sub1\n jmp done\nsub1:\n add eax,27\n ret\ndone:\n ret\n",
 "rip": "mov edx, dword ptr [rip + 0x10]",
}
for name, src in tests.items():
    try:
        enc, cnt = ks.asm(src, 0x1000)
        print(name, "OK", cnt, bytes(enc).hex())
    except Exception as e:
        print(name, "FAIL", e)
