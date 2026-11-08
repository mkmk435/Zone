import contextlib
import io
import json
import os
import random
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import pobf

results = []


def run64(payload, techs, out):
    random.seed(1234)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        zone = pobf.Zone(os.path.join("original_pl", "x64", payload))
        initial_ids = {id(i) for i in zone.instructions}
        initial = len(zone.instructions)
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
    total = len(zone.instructions)
    inserted = sum(1 for i in zone.instructions if id(i) not in initial_ids)
    changed = sum(1 for i in zone.instructions
                  if id(i) in initial_ids and i.original_instruction is not None
                  and bytes(i.new_instruction.bytes) != bytes(i.original_instruction.bytes))
    return dict(arch="x64", payload=payload, tech="+".join(techs),
                instr_in=initial, instr_out=total, inserted=inserted, changed=changed,
                protected=0, nops=zone.nops_addedd,
                in_bytes=len(zone.raw_code), out_bytes=os.path.getsize(out))


payloads = ["windows_x64_messagebox.bin", "windows_x64_custom_reverse_tcp.bin",
            "windows_x64_custom_reverse_http.bin", "windows_x64_shell_reverse_tcp.bin"]

for p in payloads:
    if not os.path.exists(os.path.join("original_pl", "x64", p)):
        continue
    for techs in (["-nop"], ["-eq"], ["-bcf"]):
        out = os.path.join("tmp", f"out64_{p}_{'_'.join(techs)}.bin")
        try:
            r = run64(p, techs, out)
        except Exception:
            r = dict(arch="x64", payload=p, tech="+".join(techs), error=traceback.format_exc())
        results.append(r)
        print(json.dumps(r), flush=True)

with open(os.path.join("tmp", "measure64.json"), "w") as fh:
    json.dump(results, fh, indent=1)
print("DONE")
