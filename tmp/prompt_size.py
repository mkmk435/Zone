import sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone
from llm_technique import build_messages, TECHNIQUES
z=Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections,xrefs=z.analyze_data(timeout=30,print_strings=False,cache_path="data_cache.json",use_cache=True)
z.extract_data(sections,xrefs); z.finalize_data_refs()
cp=from_zone(z,"x64")
for key in ("eq","nop","bcf","ibp"):
    msgs=build_messages(cp, TECHNIQUES[key])
    total=sum(len(m["content"]) for m in msgs)
    print(key, "chars",total,"approx tokens",total//4)
open("tmp/prompt_eq.txt","w",encoding="utf-8").write("\n\n".join(f"### {m['role']}\n{m['content']}" for m in build_messages(cp,TECHNIQUES["eq"])))
