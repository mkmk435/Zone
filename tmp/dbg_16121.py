import sys
sys.path.insert(0,".")
import zone
z = zone.Zone("bench/harness/bin/runner_x64.exe", seed=5, verbose=False)
z.eliminate_bad_instructions(force=True)
z.equal_instructions()
z.block_permutation(probability=100, force=True)
z.bogus_control_flow(probability=100, force=True)
z.insert_random_nop(probability=100, force=True)
z._fit_growth()
target = 0x16121
for it in z.items:
    if it.new_rva == target:
        print("item new=%#x old=%s kind=%s role=%s branch=%s bytes=%s" % (
            it.new_rva, hex(it.old_rva) if it.old_rva else None, it.kind, it.role,
            it.is_branch, it.new_bytes.hex()))
        if it.old_rva:
            inside = [(hex(a),hex(b)) for a,b in z.jumptable_ranges if a <= it.old_rva < b]
            print("  old rva dentro tabelle:", inside)
            print("  in no_resize:", [(hex(a),hex(b)) for a,b in z.no_resize_ranges if a <= it.old_rva < b])
            print("  orig bytes:", it.orig_bytes.hex(), "target_old", hex(it.target_old) if it.target_old else None)
        break
print("tabelle:", [(hex(a),hex(b)) for a,b in z.jumptable_ranges])
