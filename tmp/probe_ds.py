import json, os, urllib.request
key = (open("dsk.txt", encoding="utf-8").read()).strip()
req = urllib.request.Request(
    "https://api.deepseek.com/v1/chat/completions",
    data=json.dumps({
        "model": "deepseek-flash",
        "messages": [
            {"role": "system", "content": "You are a terse assistant."},
            {"role": "user", "content": "Say exactly: hello"},
        ],
        "temperature": 0.0,
        "max_tokens": 256,
        "stream": False,
    }).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    method="POST")
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    print(json.dumps(data, indent=2)[:6000])
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:3000])
