import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from llm_payload import canonicalize, assemble, validate
from keystone import *
ks=Ks(KS_ARCH_X86,KS_MODE_64)
code=bytes(ks.asm("_start:\n mov eax,1\n jmp L_5\nL_5:\n ret",0)[0])
cp=canonicalize(code,b"","x64")
# uppercase labels in output
out=cp.source.replace("L_5","L_5").upper().replace("_START","_start")
# uppercase is wrong for x64 regs; do targeted replace instead
out=cp.source.replace("L_5","L_5")
out=out.replace("_start:","_start:").replace("L_5:","L_5:")
# make labels uppercase only
import re
out=re.sub(r"\b(L|RET|DATA)_([0-9a-f]+)\b", lambda m: f"{m.group(1)}_{m.group(2).upper()}", cp.source)
asm=assemble(out,cp)
print("ok",len(asm.payload),validate(asm,cp,technique="eq").ok)
