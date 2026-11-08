import contextlib
import io
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import pobf
import pobf86


def count_stats(zone):
    initial = getattr(zone, "_initial_ids", set())
    total = len(zone.instructions)
    inserted = sum(1 for i in zone.instructions if id(i) not in initial)
    changed = 0
    for i in zone.instructions:
        if id(i) in initial and i.original_instruction is not None:
            if bytes(i.new_instruction.bytes) != bytes(i.original_instruction.bytes):
                changed += 1
    return total, inserted, changed


def run(arch, payload, techs, out):
    mod = pobf86 if arch == "x86" else pobf
    path = os.path.join(ROOT, "original_pl", arch, payload)
    random.seed(1234)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        zone = mod.Zone(path)
        zone._initial_ids = {id(i) for i in zone.instructions}
        initial = len(zone.instructions)
        if arch == "x86" and any(t in techs for t in ("-eq", "-nop", "-bcf")):
            zone.mark_data_ranges32()
        protected = len(getattr(zone, "data_instruction_ids", set()))
        try:
            zone.create_jmp_table()
        except Exception:
            pass
        zone.create_label_table()
        for t in techs:
            if t == "-eq":
                zone.equal_instructions()
            elif t == "-nop":
                zone.insert_random_nop()
            elif t == "-bcf":
                zone.bogus_control_flow()
        zone.update_label_table()
        zone.write_file(out)
    total, inserted, changed = count_stats(zone)
    in_size = len(zone.raw_code)
    out_size = os.path.getsize(out)
    return {
        "arch": arch, "payload": payload, "tech": "+".join(techs),
        "instr_in": initial, "instr_out": total, "inserted": inserted,
        "changed": changed, "protected": protected,
        "in_bytes": in_size, "out_bytes": out_size,
    }


jobs = []
for arch, payloads in (
    ("x86", ["windows_messagebox.bin", "windows_custom_reverse_tcp.bin",
             "windows_custom_reverse_http.bin", "windows_shell_reverse_tcp.bin"]),
    ("x64", ["windows_x64_messagebox.bin", "windows_x64_custom_reverse_tcp.bin",
             "windows_x64_custom_reverse_http.bin", "windows_x64_shell_reverse_tcp.bin"]),
):
    for p in payloads:
        if not os.path.exists(os.path.join(ROOT, "original_pl", arch, p)):
            continue
        for techs in (["-nop"], ["-eq"], ["-bcf"]):
            jobs.append((arch, p, techs))

rows = []
for arch, p, techs in jobs:
    out = os.path.join(ROOT, "tmp", f"out_{arch}_{p}_{'_'.join(techs)}.bin")
    try:
        rows.append(run(arch, p, techs, out))
    except Exception as e:
        rows.append({"arch": arch, "payload": p, "tech": "+".join(techs), "error": repr(e)})

hdr = f"{'arch':4s} {'payload':38s} {'tech':5s} {'in':>5s} {'out':>5s} {'ins':>5s} {'chg':>5s} {'prot':>5s} {'bytes':>12s}"
print(hdr)
print("-" * len(hdr))
for r in rows:
    if "error" in r:
        print(f"{r['arch']:4s} {r['payload']:38s} {r['tech']:5s} ERROR {r['error']}")
        continue
    print(f"{r['arch']:4s} {r['payload']:38s} {r['tech']:5s} {r['instr_in']:5d} {r['instr_out']:5d} "
          f"{r['inserted']:5d} {r['changed']:5d} {r['protected']:5d} "
          f"{r['in_bytes']:6d}->{r['out_bytes']:6d}")
