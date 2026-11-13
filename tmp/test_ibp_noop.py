import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from keystone import *
from llm_payload import canonicalize, assemble, validate
ks=Ks(KS_ARCH_X86,KS_MODE_64)
code=bytes(ks.asm("_start:\n mov eax,1\n add eax,2\n sub eax,3\n mov dword ptr [rcx],eax\n ret",0)[0])
cp=canonicalize(code,b"","x64")
asm=assemble(cp.source,cp)
rep=validate(asm,cp,technique="ibp")
print(rep.ok); print(rep.errors); print(rep.warnings)
