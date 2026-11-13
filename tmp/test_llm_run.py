import sys, re
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone
from llm_technique import LLMOptions, run
z = Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections, xrefs = z.analyze_data(timeout=30, print_strings=False, cache_path="data_cache.json", use_cache=True)
z.extract_data(sections, xrefs); z.finalize_data_refs()
cp = from_zone(z, "x64")
# mock eq response
lines=[]
for line in cp.source.splitlines():
    s=line.strip()
    if s == "xor rdx, rdx": lines += ["    mov rdx, 0", "    test rdx, rdx"]
    elif s == "xor r9, r9": lines += ["    mov r9, 0", "    test r9, r9"]
    elif s == "xor rax, rax": lines += ["    mov rax, 0", "    test rax, rax"]
    elif s == "sub al, 0x20": lines.append("    add al, 0xe0")
    elif s == "add r9d, eax": lines.append("    lea r9d, [r9d + eax]")
    elif s == "add r8, rdx": lines.append("    lea r8, [r8 + rdx]")
    elif s == "xor rcx, rcx": lines += ["    mov rcx, 0", "    test rcx, rcx"]
    else: lines.append(line)
open("tmp/mock_eq.txt","w",encoding="utf-8").write("```asm\n"+"\n".join(lines)+"\n```\n")
opts=LLMOptions(technique="eq", arch="x64", mock_response="tmp/mock_eq.txt",
                dump_prompt="tmp/llm_prompt.txt", dump_response="tmp/llm_resp.txt")
res=run(cp, opts)
print("result",len(res.payload),res.attempts,res.report.summary())
open("tmp/llm_run_mock.bin","wb").write(res.payload)
