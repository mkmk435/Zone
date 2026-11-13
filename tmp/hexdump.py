code=open("original_pl/x64/windows_x64_messagebox.bin","rb").read()
for off in range(0xd0, len(code), 16):
    chunk=code[off:off+16]
    print(f"{off:04x}  {chunk.hex(' '):<48}  {''.join(chr(b) if 32<=b<127 else '.' for b in chunk)}")
