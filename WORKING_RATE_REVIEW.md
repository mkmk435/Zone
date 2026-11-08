# Working-rate review: data extraction and morphing

This is a follow-up review of the current `pobf.py` / `symbolic_payload_coverage.py`
implementation, focused on **how often extraction succeeds** and on correctness
risks, not on stylistic cleanup.

The headline: the messagebox path works, but the extractor is currently limited
to payloads whose linear sweep covers the whole file. On this machine the sweep
is truncated for **26 of the 38 x64 payloads** because Capstone 5.0.1's
`skipdata` is broken (the project asks for 5.0.0.post1). That is both a
working-rate problem and a correctness problem.

---

## 1. Evidence: the sweep is truncated on most payloads

Measured with `capstone.Cs(CS_ARCH_X86, CS_MODE_64)`, `skipdata=True`,
`detail=True`, on `original_pl/x64/*.bin`:

| Payload group | Size range | Swept | Coverage |
|---|---:|---:|---:|
| `*winhttp*`, `*winhttps*` (6) | 944–1021 | 282 | **27–30%** |
| `*_http.bin`, `*_https.bin` (6) | 706–811 | 256 | **32–36%** |
| `*_tcp_uuid.bin` (2) | 551 | ~362 | 66% |
| `*bind_tcp_uuid*` (3) | 540 | 403–415 | 75–77% |
| `*_rc4.bin` (8) | 632–650 | 522–540 | 83% |
| `messagebox.bin` | 313 | 282 | 90% |
| `*_tcp` non-uuid, `bind` non-uuid (12) | 425–551 | full | 100% |

The sweep stops at the first byte Capstone cannot decode. For the HTTP family
it stops at `0x100`; for winhttp at `0x11a`. Everything after that is invisible
to:

* `find_data_and_refs()` — it iterates `self.instructions` only;
* `extract_data()` — it uses the xrefs from that scan;
* `rebuild_instructions_from_bytes()` — it uses the same `self.cs.disasm`;
* the `sweep_coverage` check, which then aborts extraction.

This is why the HTTP extraction failed:

```text
[extract] keep 0x198+163: no supported operand references the data
REBUILT 200 INSTRUCTIONS (408/789 bytes)
RuntimeError: disassembly covered 408 of 789 bytes;
             refusing to extract data from a partially disassembled payload
```

The guard is doing the right thing (refusing to write a broken payload), but the
working rate is low.

### Quick win

Pin the Capstone version the README already requires:

```sh
python -m pip install "capstone==5.0.0.post1"
```

That alone should restore the full sweep on this corpus. The code should still
detect the broken case, because depending on a specific wheel is fragile.

---

## 2. Correctness bug: a section with no xref is moved

`extract_data()` treats "no xrefs" as "no references to fix" and moves the
section anyway (`movable = ...`). That is only safe if the reference scan is
complete. It is not, for the payloads above.

Concrete case, `windows_x64_custom_reverse_http.bin`:

* sections: `0xfa` (User-Agent, 84 B), `0x16a` (`127.0.0.1`, 10 B),
  `0x198` (URI, 163 B);
* current sweep stops at `0x100`;
* current xrefs: only `0xf5 -> 0xfa` (UA getpc) and a false `0x4d -> 0x20b`
  (the `cmp ..., 0x20b` PE magic);
* `0x16a` has **no xref** and is considered movable; `0x198` is kept only
  because the false `cmp` reference classifies it as unsupported.

But a manual skipdata sweep finds a real getpc for the IP:

```text
0x165: call 0x174   ; pushes 0x16a
0x16a: "127.0.0.1\0"
0x174: pop rdx      ; rdx = 0x16a
```

and the URI has a **late-pop** getpc:

```text
0x193: e8 a3 00 00 00   call 0x23b   ; pushes 0x198 (URI start)
0x198: "/7FQjpl..."                 ; 163 B
0x23b: mov rcx, rax
0x23e: push rbx
0x23f: pop rdx
0x240: pop r8                        ; r8 = 0x198
```

The current getpc rule requires the callee to be a `pop` immediately; here the
callee is `mov rcx, rax`, and the pop comes after stack-neutral instructions.
The ref is missed. If the coverage guard did not abort, `0x16a` would be NOPed
and appended while the call at `0x165` still pushes the old address — a broken
payload. (`0x198` happens to stay in place only because of the false positive.)

### Fix

1. Require at least one **verified** reference for every moved section by
   default. Add `--allow-unreferenced` for genuinely dead data.
2. Add a raw byte-level getpc scan that does not depend on the linear sweep
   (section 3).
3. After extraction, audit the original bytes: any `call` whose pushed address
   falls into a moved section and has no fixup → abort, do not write.

---

## 3. Missed getpc forms

Current detection (`find_data_and_refs`, `pobf.py:1005`) handles:

```asm
call target
[data]
target: pop r64
```

It does not handle:

1. **Late pop after stack-neutral code**

   ```asm
   call target        ; pushes data start
   [data]
   target: mov rcx, rax
           push rbx
           pop rdx
           pop r8     ; consumes the pushed data address
   ```

2. **`call $+5; pop reg; add/sub/lea reg, imm`**

   The pushed value is code after the call; the data address is
   `pushed ± imm`. The xref target must be computed from the `add`/`sub`/`lea`.

3. **Padding between the data and the pop**

   The current validation requires `pop.address == section_start + length`.
   Alignment NOPs or a zero pad after the string make it fail.

4. **`call $+5; pop reg; ...` where data is elsewhere**

   The scanner records the pushed address (code), not the computed data address.

### Fix

A small stack-depth simulator over the callee handles (1):

```python
depth = 0
pc = call_target
for _ in range(16):
    insn = decode(pc)
    if insn.mnemonic.startswith("push"):
        depth += 1
    elif insn.mnemonic.startswith("pop"):
        if depth == 0:
            return insn.operands[0].reg   # this pop consumes the call's slot
        depth -= 1
    elif insn.mnemonic in ("add", "sub") and insn.operands[0].reg == "rsp":
        ...
    elif insn.group(CS_GRP_JUMP | CS_GRP_CALL | CS_GRP_RET):
        return None
    pc += insn.size
```

Then record the getpc with the register of the consuming pop, not the callee's
first instruction.

For (2), after the pop, look for one of:

```text
add reg, imm
sub reg, -imm
lea reg, [reg + imm]
```

and compute the effective target. If it lands in a data range, record it; the
extraction rewrite must then replace the pop + adjustment, not the call alone.

For (3), allow a gap of `0x90`/`0x00` bytes after the section before the pop and
rewrite the whole `[call, pop_end)` region.

### A raw getpc scan is the highest-ROI safety net

Scan every byte for a `call rel32` whose return address is inside a data
section:

```python
for off in range(len(raw) - 5):
    if raw[off] != 0xE8:
        continue
    ret = off + 5
    for section in sections:
        if ret == section.start:          # pushed data start
            target = ret + int.from_bytes(raw[off+1:off+5], "little", signed=True)
            if decode(target) is getpc_pop_or_late_pop(...):
                add_xref(off, ret, section.length)
```

This catches getpc calls that the linear sweep never decoded, and it is cheap.
It also gives a second opinion before moving a "no-xref" section.

---

## 4. The data classifier still misses non-string payload data

`identify_data` only emits:

* printable ASCII/UTF-16LE strings;
* `cfg_data` from CFGFast;
* residual `outside_cfg` ranges.

Binary blobs (keys, shellcode stages, encoded configs) are usually
`outside_cfg` and are skipped by default. The call/pop gap is strong evidence of
data even when it is not printable. A `call_gap` kind would let the extractor
move any gap that a `call` skips over and a `pop` consumes, provided the bytes
are not executed and not in CFG code.

Also, `call_pop_gaps` currently only *corroborates strings*. It could seed
sections:

```text
for each call -> pop gap:
    if gap not executed and gap not reachable code:
        emit section(kind="call_gap", start=gap_start, length=pop - gap_start)
```

That would increase discovery on the HTTP/winhttp family without `--extract-unknown`.

---

## 5. Symbolic coverage improvements

The plugin classifies data; its blind spots become extractor blind spots.

1. **Seed the second CFG pass with *all* observed block entries**, not one per
   unclassified range. The current one-seed-per-range heuristic can miss
   adjoining blocks reached by indirect jumps.
2. **Instrument memory reads** (`state.inspect.b("mem_read", ...)`) and record
   concrete addresses. This gives a second, execution-backed xref source and
   corroborates data ranges.
3. **Model a minimal PEB/TEB.** Most Windows shellcode does
   `mov rdx, gs:[0x60]` and walks the loader list. With a fake TEB/PEB and a
   fake `kernel32` export table, the resolver could be executed far enough to
   observe API calls. This is the largest structural improvement, but also the
   most work.
4. **Avoid base-0 aliasing** (already done in the library): keep the internal
   nonzero analysis base and translate addresses.
5. **State exploration**: the serial one-state-at-a-time loop is slow. LoopSeer,
   Veritesting, or state merging could increase observed coverage within the
   same timeout. Test before adopting; they can also change path selection.
6. **The cache should record coverage quality.** Right now a 4-second run can be
   reused by a 120-second request. Either re-run when
   `requested_timeout > cached_timeout`, or store `stop_reason` /
   `coverage_status` and expose it on a hit. This is a quality issue, not just
   speed.

---

## 6. Morphing fragility

* **Short branches are only protected in `insert_random_nop`.** `-eq` can change
  instruction sizes and push a `jrcxz`/`loop` out of the 8-bit range;
  `-bcf`/`-ibp` can insert code between a branch and its target. The only
  current answer is the `jrcxz` restart/abort path.
* **Global repair is better than restart.** After every size-changing morph,
  scan all `jrcxz`/`loop` instructions; if the distance exceeds ±127, expand the
  short form to a long form, e.g.:

  ```asm
  jrcxz +2        ; if rcx == 0, skip the next jmp
  jmp fallthrough
  jmp target
  ```

  or use `eliminate_jrcxz_instructions()`. Then the restart hack can be removed.
* **`-bcf`/`-ibp` are not verified** with extraction. On the messagebox,
  `-bcf` pushes the `jrcxz` distance to 130–151 every run and always ends in the
  retry cap.
* **`-eq` can be tested deterministically** with a fixed `random.seed` during
  regression tests; currently the outputs vary run to run.

**Update (implemented):** `--eliminate-bad-instructions` (`-ebi`) now performs
this expansion for `jrcxz`/`loop`-family branches in both the normal and
`--extract-data` paths. `-eq`, `-nop`, and `-bcf` complete on the messagebox
sample with it; the `jrcxz` restart is not entered. The old
`eliminate_jrcxz_instructions()` / `eliminate_loop_instructions()` are no longer
used by `start()`.

The `-bcf` instability was a separate bug: the inserted `je` used a
hand-computed target that later random insertions could invalidate. The `je` is
now registered in `short_label_table`, so `update_label_table()` repatches it.
Measured with `ploader.exe` on 10 independent `-xd -bcf -ebi` payloads:
**10/10 valid after the fix, 3/10 before it**.

---

## 7. Other concrete code defects

### 7.1 `create_jmp_table` uses an undefined `self.pe`

`pobf.py:2005`:

```python
for n, i in enumerate(self.jump_table):
    ...
    addr = self.pe.get_dword_at_rva(i + x*4)
```

`self.pe` is never assigned in `pobf.py` (it is a raw-payload tool). If a
payload contains the `mov` + `add` + `jmp reg` pattern, `jump_table` becomes
non-empty and this raises `AttributeError`. `start()` wraps the call in
`try/except`, but `eliminate_instr()` does not. Guard it or remove the PE path
from the raw tool.

### 7.2 `write_file` truncates after morphing without extraction

If the sweep did not cover the payload and `morph_applied` is true, the tail is
not written (there is a warning now). This is a pre-existing consequence of the
Capstone issue; the full sweep fixes it.

### 7.3 Immediate false positives

`find_data_and_refs` still reports `cmp ..., 0x20b` as a data xref. Extraction
rejects the section, but `--find-data` output remains noisy. Restrict immediate
xrefs to `mov`/`movabs`/`push` at scan time (not only at extraction time), or
add a `--strict-immediates` switch.

### 7.4 Cache timeout reuse

See 5.6. A short-timeout entry can mask a better run. This is not a crash, but
it affects result quality.

### 7.5 Library/CLI base inconsistency

`find_data_sections()` rebases low bases internally; the CLI `main()` does not
and only warns. The README documents this, but it is an easy source of
different results for the same input.

### 7.6 `update_instr` writes `dict.txt` on every call

A debugging side effect in a hot path. It also runs on every label-table
iteration. Remove or gate it behind a debug flag.

### 7.7 Dead PE code

`write_pe_file`, `adjust_reloc_table`, `adjust_jmp_table` reference `self.pe`,
`self.code_raw_start`, `self.original_entry_point`, which are not set by
`Zone`. They are unreachable in the raw path but are a trap for future edits.
Either delete them from `pobf.py` or move them to `zone.py`.

---

## 8. Prioritized roadmap

| Priority | Change | Why | Effort |
|---|---|---|---|
| P0 | Pin Capstone 5.0.0.post1 and detect broken skipdata | 26/38 payloads have partial sweeps | S |
| P0 | Never move a section with no verified ref (`--allow-unreferenced` opt-in) | Prevents broken payloads when refs are missed | S |
| P0 | Raw byte-level getpc scan (including late pop) | Catches refs outside the sweep; validates no-ref sections | M |
| P1 | Full manual skipdata sweep (`ByteInstruction` fallback) | Removes dependence on the wheel; restores refs in the tail | M |
| P1 | `call_gap` data class / seed sections from call/pop gaps | Finds non-string data | M |
| P1 | Handle `call $+5; pop; add/lea`; allow padding before pop | More getpc variants | M |
| P1 | Cache: re-run when requested timeout > cached; store coverage | Result quality | S |
| P2 | Global short-branch repair after morphing | `-eq`/`-bcf`/`-ibp` working rate | M |
| P2 | Test/fix `-bcf`/`-ibp` with extraction; drop the restart hack | Morphing rate | M |
| P2 | Guard `create_jmp_table` against missing `self.pe` | Latent crash | S |
| P3 | Seed CFG with all observed block entries | More code coverage | S |
| P3 | `mem_read` instrumentation | Execution-backed data refs | M |
| P3 | Minimal PEB/TEB/export-table model | Unlocks Windows shellcode | L |
| P4 | Clean dead PE code, `dict.txt` side effect, base consistency | Maintainability | S |

### Suggested first batch (highest ROI, low risk)

1. Add the raw getpc scan and use it in `find_data_and_refs` and in
   `extract_data` validation. This alone would find the HTTP IP getpc and the
   late-pop URI variant.
2. Require a verified ref before moving a section; add `--allow-unreferenced`.
3. Log/abort if any original `call` pushes into a moved section and has no fixup.
4. Compare cache timeout and refresh on a larger request.
5. Add a startup check for Capstone skipdata support; print the version and a
   clear warning if the sweep is truncated.

### What not to do

* Do not simply bypass the `sweep_coverage` guard to increase the "success"
  count: it will produce broken payloads.
* Do not merge `outside_cfg` into data by default; it is often unreachable code.
* Do not compact the code before the ref discovery is complete; relocation would
  turn one missed ref into a global breakage.

---

## 9. Short conclusion

The extraction architecture is sound: symbolic classification -> static xref
scan -> size-preserving rewrite -> finalize after morphing. The main weakness is
that the xref scan is only as complete as the linear sweep, and the sweep is
truncated on most of the corpus. The second weakness is that "no xref" is
currently treated as "safe to move", which can silently break a payload when the
sweep missed a reference.

Fix the sweep and the reference completeness, and the working rate should move
from "messagebox and a few full-coverage payloads" to most of the corpus.
