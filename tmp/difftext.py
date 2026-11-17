import sys
a=open("ploader.exe","rb").read(); b=open("tmp/one.exe","rb").read()
# .text raw offset 0x400, va 0x1000
for off in range(0x400,0x400+0x40):
    if a[off]!=b[off]:
        print("primo byte diverso in .text off %#x rva %#x: %02x -> %02x" % (off, off-0x400+0x1000, a[off], b[off]))
        break
else:
    print("nessuna differenza nei primi 64 byte")
a2=a[0x400:0x400+0x100]; b2=b[0x400:0x400+0x110]
print("orig:", a2[:0x60].hex())
print("nuovo:", b2[:0x66].hex())
