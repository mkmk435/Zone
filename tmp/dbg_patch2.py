import sys

sys.path.insert(0, ".")
import zone_v2 as Z

z = Z.Zone(sys.argv[1], verbose=False)
z.equal_instructions()
z.insert_random_nop(10)
blob = z._emit_text()
image = z._build_image(blob)

code_items = [i for i in z.items if i.kind == "insn"]
ranges = {}
for it in code_items:
    ranges[it.new_rva] = it

writes = []
orig = z._write_value


def spy(img, new_rva, width, value):
    writes.append((new_rva, width, value))
    return orig(img, new_rva, width, value)


z._write_value = spy
before = bytes(image)
z._apply_patches(image)
after = bytes(image)
z._write_value = orig

import bisect
starts = sorted(ranges)
bad = 0
for new_rva, width, value in writes:
    pos = bisect.bisect_right(starts, new_rva) - 1
    if pos < 0:
        continue
    it = ranges[starts[pos]]
    if it.new_rva <= new_rva < it.new_rva + it.size and it.kind == "insn":
        bad += 1
        if bad <= 8:
            print("patch dentro istruzione: site(new)=%#x width=%d value=%#x item=%r"
                  % (new_rva, width, value, it))
print("patch che finiscono dentro istruzioni:", bad, "di", len(writes))
# attribuisci
for site, width, mode, target, constant in z.patches:
    ns = z.map_point(site)
    pos = bisect.bisect_right(starts, ns) - 1
    if pos < 0:
        continue
    it = ranges[starts[pos]]
    if it.new_rva <= ns < it.new_rva + it.size:
        print("PATCH", mode, "site", hex(site), "->", hex(ns), "in", hex(it.old_rva))
        break
