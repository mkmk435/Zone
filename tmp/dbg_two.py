import sys, struct
sys.path.insert(0,".")
import zone
z = zone.Zone("bench/harness/bin/runner_x64.exe", verbose=False)
print("bytes @0x10d12:", z.read(0x10d12, 40).hex())
print("prev insn:", z.insns.get(0x10d0e))
print()
print("bytes @0x15639:", z.read(0x15639, 48).hex())
for off in range(3, 40, 4):
    site = 0x15639 + off
    v = z.read_u32(site)
    print("  entry %#x = %#x  in insns=%s decodable=%s" % (site, v, v in z.insns, z._decode_one(v) is not None))
print()
print("jump tables trovate:", len(z.jump_tables), [hex(t['base']) for t in z.jump_tables])
