import pefile
pe = pefile.PE("tmp/test_pe.exe")
data = open("tmp/test_pe.exe","rb").read()
s = pe.sections[0]
off = s.PointerToRawData
print("entry", hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint), "text raw off", hex(off), "vsize", hex(s.Misc_VirtualSize))
print("bytes:", data[off:off+56].hex())
from capstone import *
cs = Cs(CS_ARCH_X86, CS_MODE_64); cs.detail=True
for i in cs.disasm(data[off:off+56], s.VirtualAddress):
    print("%#x %-24s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
