import struct

raw = bytearray(open(r"C:\Users\ubu\Desktop\Zone\original_pl\x86\windows_messagebox.bin", "rb").read())
n = len(raw)
pad = (-n) % 16
stub1 = n + pad
data1 = stub1 + 5
stub2 = data1 + 11
data2 = stub2 + 5

blob = bytearray()
blob += b"\x90" * pad
blob += b"\xE8" + struct.pack("<i", 0xA6 - (stub1 + 5))      # call 0xa6
blob += b"user32.dll\x00"
blob += b"\xE8" + struct.pack("<i", 0xD5 - (stub2 + 5))      # call 0xd5
blob += b"Hello, from MSF!\x00"

for site, target in ((0x96, stub1), (0xBF, stub2)):
    disp = target - (site + 5)
    raw[site] = 0xE9
    raw[site + 1:site + 5] = struct.pack("<i", disp)

out = bytes(raw) + bytes(blob)
open(r"C:\Users\ubu\Desktop\Zone\tmp\x86_mb_stubonly.bin", "wb").write(out)
print("size", len(out), "stub1", hex(stub1), "data1", hex(data1),
      "stub2", hex(stub2), "data2", hex(data2))
