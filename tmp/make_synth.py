import struct

data = b"SECRETDATA123\x00"
call_size = 5
T = call_size + len(data)

code = bytearray()
code += b"\xE8" + struct.pack("<i", T - call_size)  # call T
code += data
assert len(code) == T
code += b"\x5E"          # pop esi
code += b"\x8A\x06"      # mov al, [esi]
code += b"\x3C\x53"      # cmp al, 'S'
code += b"\x75\x02"      # jne fail
code += b"\xEB\xFE"      # jmp $
code += b"\xC3"          # fail: ret

open(r"C:\Users\ubu\Desktop\Zone\tmp\synth_getpc.bin", "wb").write(bytes(code))
print("size", len(code), "T", hex(T))
print(code.hex(" "))
