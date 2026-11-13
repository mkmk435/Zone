import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from keystone import *
from llm_payload import canonicalize
from llm_technique import LLMOptions, run
from test_asm_wrap import Runner
ks=Ks(KS_ARCH_X86,KS_MODE_64)
code=bytes(ks.asm("_start:\n mov eax, 0x1234\n add eax, 1\n mov dword ptr [rcx], eax\n ret",0)[0])
cp=canonicalize(code,b"","x64")
print(cp.source)
out="""```asm
_start:
L_0:
    mov eax, 0x1234
    jmp block_a
block_b:
    mov dword ptr [rcx], eax
    ret
block_a:
    add eax, 1
    jmp block_b
```"""
open("tmp/mock_ibp.txt","w",encoding="utf-8").write(out)
opts=LLMOptions(technique="ibp",arch="x64",mock_response="tmp/mock_ibp.txt")
res=run(cp,opts)
print("result",len(res.payload),res.report.summary())
runner=Runner()
expected=runner(code)
got=runner(res.payload)
print("expected",expected[:8] if expected else None)
print("got     ",got[:8] if got else None)
print("match", expected==got)
