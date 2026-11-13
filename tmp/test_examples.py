import sys, re
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from llm_technique import TECHNIQUES
from keystone import *
for key,spec in TECHNIQUES.items():
    text=spec.examples
    out=text.split("output:",1)[1].strip()
    # strip possible trailing text
    ks=Ks(KS_ARCH_X86,KS_MODE_64)
    try:
        e,_=ks.asm(out,0); print(key,"OK",len(e),bytes(e).hex())
    except Exception as ex:
        print(key,"ERR",ex); print(out)
