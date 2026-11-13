text = open("llm_data.py", encoding="utf-8").read()
for i,line in enumerate(text.splitlines(),1):
    if i in (149,392,490):
        for ch in line:
            if ord(ch) > 127:
                print(i, hex(ord(ch)), repr(ch))
