for name in ("llm_data.py",):
    text = open(name, encoding="utf-8").read()
    for i,line in enumerate(text.splitlines(),1):
        if i in (149,392,490):
            print(i, repr(line))
