import sys
sys.path.insert(0,".")
import zone
z = zone.Zone("tmp/test_pe.exe", seed=3, verbose=False)
print("no_resize:", [(hex(a),hex(b)) for a,b in z.no_resize_ranges])
print("no_insert:", [(hex(a),hex(b)) for a,b in z.no_insert_ranges])
print("jump tables:", z.jump_tables)
print("jumptable ranges:", [(hex(a),hex(b)) for a,b in z.jumptable_ranges])
