import contextlib, io, os, sys
ROOT = r"C:\Users\ubu\Desktop\Zone"
sys.path.insert(0, ROOT); os.chdir(ROOT)
import pobf86
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    z = pobf86.Zone(os.path.join("original_pl", "x86", "windows_messagebox.bin"))
a = z._pii_stub_insns_32(0, 0x5fd)
b = z._pii_stub_insns_32(0x7e0, 0x5fd)
print("placeholder:", [(insn.mnemonic, insn.size, insn.op_str) for insn in a])
print("total a:", sum(i.size for i in a))
print("final:", [(insn.mnemonic, insn.size, insn.op_str) for insn in b])
print("total b:", sum(i.size for i in b))
