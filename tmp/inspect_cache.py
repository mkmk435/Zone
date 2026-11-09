import json
d = json.load(open('data_cache.json'))
print(type(d), len(d))
for k, v in list(d.items())[:5]:
    print(k, type(v), str(v)[:200])
