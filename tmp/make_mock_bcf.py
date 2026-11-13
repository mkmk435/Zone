import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone
z=Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections,xrefs=z.analyze_data(timeout=30,print_strings=False,cache_path="data_cache.json",use_cache=True)
z.extract_data(sections,xrefs); z.finalize_data_refs()
cp=from_zone(z,"x64")
lines=cp.source.splitlines()
block="""    pushfq
    push rax
    xor eax, eax
    jnz bogus_1
    jmp real_1
bogus_1:
    nop
    mov rdx, rdx
real_1:
    pop rax
    popfq"""
out=[]
for line in lines:
    out.append(line)
    if line.strip()=="_start:":
        out.append(block)
open("tmp/mock_bcf.txt","w",encoding="utf-8").write("```asm\n"+"\n".join(out)+"\n```\n")
print("ok")
