import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from keystone import *
from llm_payload import canonicalize, assemble, validate
from test_asm_wrap import Runner
ks=Ks(KS_ARCH_X86,KS_MODE_64)
src="""
_start:
    lea rax, [rip + target]
    mov byte ptr [rcx], 1
    jmp rax
target:
    mov byte ptr [rcx + 1], 2
    ret
"""
code=bytes(ks.asm(src,0)[0])
cp=canonicalize(code,b"","x64")
print(cp.source)
asm=assemble(cp.source,cp)
rep=validate(asm,cp,technique="eq")
print(rep.summary(),rep.errors,rep.warnings)
run=Runner(); print("orig",run(code)[:4]); print("new ",run(asm.payload)[:4])
