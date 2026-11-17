import sys
needles = [bytes.fromhex("1b641300173412 00".replace(" ","")), bytes.fromhex("17341200"), bytes.fromhex("1b641300")]
for path in sys.argv[1:]:
    data = open(path, "rb").read()
    print(path, len(data))
    for n in needles:
        hits = []
        start = 0
        while True:
            i = data.find(n, start)
            if i < 0: break
            hits.append(i); start = i+1
        print("  ", n.hex(), "->", len(hits), [hex(h) for h in hits[:6]])
