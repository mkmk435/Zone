import sys, re
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from llm_technique import TECHNIQUES
from llm_payload import canonicalize, assemble, validate
from keystone import *
for key,spec in TECHNIQUES.items():
    text=spec.examples
    inp=text.split("input:",1)[1].split("output:",1)[0].strip()
    out=text.split("output:",1)[1].strip()
    ks=Ks(KS_ARCH_X86,KS_MODE_64)
    code=bytes(ks.asm(inp,0)[0])
    cp=canonicalize(code,b"", "x64")
    asm=assemble(out,cp)
    rep=validate(asm,cp,technique=key,min_similarity=spec.min_similarity)
    print(key,rep.summary(),rep.errors)
