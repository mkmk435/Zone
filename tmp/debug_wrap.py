"""Debug helper: show the wrap block/item that fails verification."""
import sys
import os

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wrap_snapshot")
sys.path.insert(0, SNAP)
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wrap_run"))

import asm_wrap


def patched_verify(self, buffer, get_bytes):
    for item in self.items:
        base = self.new_address[item.key]
        raw = bytes(buffer[base:base + len(item.data)])
        got = self._disasm_one(raw, base)
        expected = self._insn[item.key]
        if got is None or got.mnemonic != expected.mnemonic:
            block = next((b for b in self.blocks if item in b.items), None)
            index = self.items.index(item)
            prev = self.items[index - 1] if index else None
            nxt = self.items[index + 1] if index + 1 < len(self.items) else None
            print("=== VERIFY FAILURE ===")
            print("item addr", hex(item.addr), "data", item.data.hex(),
                  "len", len(item.data), "base", hex(base))
            print("expected", expected.mnemonic, expected.op_str, "size",
                  expected.size)
            print("got", (got.mnemonic, got.op_str, got.size) if got else None)
            print("block", block.kind if block else None,
                  "start", hex(block.start) if block else None,
                  "size", block.size if block else None,
                  "glue", block.glue_offset if block else None,
                  "used", block.used if block else None)
            print("prev", prev and (hex(prev.addr), prev.data.hex()),
                  "->", prev and hex(self.new_address[prev.key]))
            print("next", nxt and (hex(nxt.addr), nxt.data.hex()),
                  "->", nxt and hex(self.new_address[nxt.key]))
            lo = max(0, base - 12)
            hi = min(len(buffer), base + 20)
            print("buffer", lo, "..", hi, buffer[lo:hi].hex())
            print("item bytes in buffer", buffer[base:base + len(item.data)].hex())
            raise SystemExit(1)
    asm_wrap.AssemblyWrapping._real_verify(self, buffer, get_bytes)


asm_wrap.AssemblyWrapping._real_verify = asm_wrap.AssemblyWrapping._verify
asm_wrap.AssemblyWrapping._verify = patched_verify

sys.argv = ["pobf.py"] + sys.argv[1:]
import pobf
pobf.start(None)
