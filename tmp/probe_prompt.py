import json, sys
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone
from llm_technique import LLMOptions, build_messages, TECHNIQUES, DeepSeekClient
z = Zone(r"C:\Users\ubu\Desktop\Zone\tmp\synth_ret.bin")
cp = from_zone(z, "x64")
msgs = build_messages(cp, TECHNIQUES["eq"])
key = open("dsk.txt", encoding="utf-8").read().strip()
opts = LLMOptions(technique="eq", arch="x64", api_key=key,
                  model="deepseek-flash", max_tokens=4096, timeout=120)
client = DeepSeekClient(opts)
try:
    data = client._request(msgs)
    print("KEYS", list(data.keys()))
    ch = data.get("choices", [])
    print("CHOICES", len(ch))
    if ch:
        msg = ch[0].get("message", {})
        print("MSG KEYS", list(msg.keys()))
        print("FINISH", ch[0].get("finish_reason"))
        print("CONTENT LEN", len(msg.get("content") or ""))
        print("REASONING LEN", len(msg.get("reasoning_content") or ""))
        print("CONTENT", repr((msg.get("content") or "")[:2000]))
        print("REASONING", repr((msg.get("reasoning_content") or "")[:2000]))
    print("USAGE", data.get("usage"))
except Exception as e:
    print("ERR", type(e).__name__, e)
