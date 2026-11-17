import bisect
import sys

sys.path.insert(0, ".")
import zone_v2 as Z

path = sys.argv[1]
for seed in range(0, int(sys.argv[2]) if len(sys.argv) > 2 else 12):
    try:
        z = Z.Zone(path, seed=seed, verbose=False)
        z.equal_instructions()
        z.insert_random_nop(10)
        blob = z._emit_text()
        image = z._build_image(blob)
        z._patch_headers(image)
        before = bytes(image)
        z._apply_patches(image)
        after = bytes(image)

        # ogni item deve mantenere i propri byte, tranne i campi imm/disp
        # che le patch possono legittimamente aggiornare
        bad = []
        for item in z.items:
            if item.kind != "insn" or not item.new_bytes:
                continue
            off = z.new_off(item.new_rva)
            got = after[off:off + len(item.new_bytes)]
            if got == item.new_bytes:
                continue
            # differenza ammessa solo se il sito e' un campo imm/disp
            enc = item.cs_insn.encoding
            allowed = set()
            if enc.imm_size:
                allowed.update(range(enc.imm_offset, enc.imm_offset + enc.imm_size))
            if enc.disp_size:
                allowed.update(range(enc.disp_offset, enc.disp_offset + enc.disp_size))
            diff = [i for i in range(len(item.new_bytes)) if got[i] != item.new_bytes[i]]
            if not diff or not set(diff) <= allowed:
                bad.append((item, diff[:8]))
        print("seed", seed, "item corrotti:", len(bad))
        for item, diff in bad[:4]:
            print("   ", item, "byte", item.new_bytes.hex(), "diff", diff)
    except Z.ZoneError as exc:
        print("seed", seed, "ZoneError:", exc)
