from keystone import *
ks=Ks(KS_ARCH_X86,KS_MODE_64)
enc,_=ks.asm("_start:\n mov eax, 1\n add eax, 2\n ret",0)
open("tmp/synth_ret.bin","wb").write(bytes(enc))
open("tmp/retry_mock.txt","w",encoding="utf-8").write("```asm\nthis is not assembly\n```\n\n---ATTEMPT---\n\n```asm\n_start:\n mov eax, 1\n add eax, 2\n ret\n```\n")
print("ok",len(enc))
