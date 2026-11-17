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
for target in (0x16119, 0x16149):
    for it in z.items:
        if it.new_rva == target:
            print("item @new %#x: kind=%s role=%s is_branch=%s old=%s bytes=%s target_old=%s target_item=%s size=%d" % (
                target, it.kind, it.role, it.is_branch,
                hex(it.old_rva) if it.old_rva else None, it.new_bytes.hex(),
                hex(it.target_old) if it.target_old else None,
                hex(it.target_item.new_rva) if it.target_item else None, it.size))
            break
    else:
        print("nessun item a", hex(target))
