import sys
sys.path.insert(0,".")
import zone
z = zone.Zone(sys.argv[1], seed=3, verbose=False)
units = z._split_blocks()
print("unita:", len(units))
blocks = [u for u in units if u[0]=="block"]
print("blocchi:", len(blocks))
for kind, key, payload in units[:14]:
    if kind == "data":
        print("  data", hex(payload.old_rva), payload.size)
    else:
        print("  block key=%s items=%d first=%s last=%s elig=%s" % (
            hex(key) if key else None, len(payload),
            hex(payload[0].old_rva), payload[-1].cs_insn.mnemonic,
            z._block_eligible(payload)))
