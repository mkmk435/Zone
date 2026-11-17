import sys
sys.path.insert(0, ".")
import zone_v2 as Z
class Z2(Z.Zone):
    def equal_instructions(self, probability=100):
        return 0
    def _can_insert_after(self, item):
        if not (0x100b <= item.old_rva < 0x1011):
            return False
        return super()._can_insert_after(item)
z = Z2("ploader.exe", seed=7, verbose=True)
z.insert_random_nop(probability=100)
z.write_pe_file("tmp/one.exe")
print("inseriti:", z.added_bytes, "item:", len(z.items))
