# ATTENTION
Right Now Zone is only somehow usable with small sized PIE payloads (both x64 and x86, especially tested with Metasploit framework payloads). so only look at the `pobf.py` and `pobf86.py`. Zone as a PE obfuscator is totally unreliable and only works/is tested against very small executables compiled by myself. Anything bigger makes Zone completely unusable. For PE implementation refer to `Zone.py`

## Disclaimer

This tool is designed and provided for educational, research, and authorized security assessment purposes only. 

Using this software against targets without prior mutual, explicit, and written consent is illegal. It is the end user's sole responsibility to comply with all applicable local, state, and international laws. 

The author(s) and contributor(s) assume no liability and are not responsible for any misuse, damage, or legal consequences caused by this program.

## LLM-assisted morphing (`--llm`)

Zone can hand one of its techniques to a DeepSeek model instead of running the
Python implementation.  The model receives a label-annotated assembly listing
of the payload and must return the **complete morphed payload as assembly**;
Zone assembles it with Keystone, appends the data blob itself, validates the
result and retries with the exact error if the answer is broken.

This is deliberately a full assembly rewrite, not a byte patch.  A local
substitution changes instruction lengths, which changes every relative branch
and every RIP-relative reference; labels let Keystone recompute all of them.

```sh
# x86-64
python pobf.py payload.bin --llm -eq  -o out.bin
python pobf.py payload.bin --llm -bcf --llm-verify messagebox -o out.bin
python pobf.py payload.bin --llm -ibp --llm-shots 2 -o out.bin
python pobf.py payload.bin --llm-data -o extracted.bin

# x86 (32-bit)
python pobf86.py payload.bin --llm -nop -o out.bin
```

Supported techniques in LLM mode: `-eq`, `-nop`, `-bcf`, `-ibp`.
`-pii`, `-ip` and `-wrap` keep using the native implementation (their layout is
part of the technique and is not delegated to the model yet).  Pass exactly one
technique flag.  `--llm-technique eq` is an alternative spelling.

The prompt includes worked examples.  `--llm-shots 1` (the default) sends the
first example; `--llm-shots 2` or `3` sends more; `--llm-shots 0` disables the
examples and leaves only the textual specification.  For `-ibp`, `--llm-shots 2`
is recommended: the second example shows a helper block moved past the done
block, and in testing it produced a larger permutation than the default single
example.  The tool rejects an `-ibp` answer whose original instruction order is
unchanged, so a no-op cannot be accepted as a successful permutation.

### API key and model

The key is read from `ZONE_LLM_API_KEY` or `DEEPSEEK_API_KEY`.  If neither is
set and stdin is a terminal, Zone asks for it with a hidden prompt.  The key is
never written to disk, to the prompt, or to the response dump.

| Variable | Default | Meaning |
|---|---|---|
| `DEEPSEEK_API_KEY` / `ZONE_LLM_API_KEY` | — | API key |
| `ZONE_LLM_MODEL` | `deepseek-flash` | Model id (`deepseek-v4-pro` also available) |
| `ZONE_LLM_BASE_URL` / `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | OpenAI-compatible base URL |
| `ZONE_LLM_TIMEOUT` | `180` | HTTP timeout (seconds) |
| `ZONE_LLM_MAX_TOKENS` | `32768` | Output token limit (reasoning tokens included) |

If the model id is not available on the account, set
`ZONE_LLM_MODEL` to one of the ids accepted by the API.  The account used
during development accepts `deepseek-flash` (the default) and
`deepseek-v4-pro`.  All values can also be passed on the command
line (`--llm-model`, `--llm-base-url`, ...).

`deepseek-flash` reasons before answering, and the reasoning tokens count
against `--llm-max-tokens`.  A small budget can be spent entirely on
reasoning, leaving an empty answer (`finish_reason=length`).  The default is
therefore 32768; lower it only if you know the payload is small.

### What Zone does around the model

1. **Data extraction first.**  With `--llm`, `-xd` runs automatically (unless
   `--llm-no-extract-data` is given).  Inline strings and getpc data cannot be
   moved safely by a language model, so Zone moves them to the appended blob
   and rewrites the references before building the prompt.  This is
   preprocessing, not the selected morphing technique.
2. **Canonical listing.**  Every direct branch target becomes a label
   (`L_*`), every getpc return address becomes `RET_*`, and every reference
   into the data blob becomes `DATA_*` / `DATA_STUB_*`.  The model never sees
   absolute code addresses and never emits the data bytes.
3. **Prompt.**  It contains the detailed technique specification, the
   constraints (flags, stack, operand size, short branches, getpc adjacency,
   string instructions, ...), a verified input/output example, and the payload
   delimited as data.  The prompt is rebuilt for every retry with the exact
   validation error and the rejected answer.
4. **Assembly and validation.**  Keystone assembles the answer.  Zone checks
   full disassembly coverage, branch targets on instruction boundaries, data
   references, `RET_*` adjacency, return-instruction count, forbidden
   instructions, and (per technique) that the original instructions were not
   dropped or reordered.
5. **Optional execution check.**  `--llm-verify messagebox` runs the output
   through `ploader.exe` / `ploader86.exe` and waits for the `#32770` dialog.
   This is the strongest check available; the default `static` mode does not
   execute the payload.

### LLM data classification (`--llm-data`)

`--llm-data` is an alternative to the symbolic `-xd`: the model classifies
which byte ranges are data, then the existing xref scanner and
`Zone.extract_data()` machinery move those ranges and rewrite every reference.

```powershell
# classify + extract only (like -xd, but LLM-classified)
python pobf.py payload.bin --llm-data -o out.bin

# classify + extract, then morph with an LLM technique
python pobf.py payload.bin --llm-data -eq -o out.bin

# x86
python pobf86.py payload86.bin --llm-data -o out86.bin
```

`--llm-data` implies `--llm`; it cannot be combined with `-xd`, `-fd` or
`--llm-no-extract-data`.  It and `-xd` are alternatives, not a pipeline.

The prompt contains a hex dump with ASCII, a linear disassembly, and
candidate printable runs.  The model returns JSON only:

```json
{"sections":[{"offset":223,"length":11,"kind":"ascii","text":"user32.dll"}]}
```

The tool then:

* checks offsets, lengths and overlaps;
* locates references to each range with the existing xref scanner;
* drops ranges with no code reference;
* refuses to move a range whose references cannot be rewritten safely;
* calls `extract_data()` and `finalize_data_refs()` on a fresh `Zone`, so a
  rejected answer never corrupts the working payload.

The model never relocates code and never rewrites a reference; that part stays
deterministic.  `--llm-data-json <file>` saves the classified ranges, their
xrefs and the token/cost statistics.  `--llm-shots` controls the worked
examples in the data-classification prompt as well.

On the x64 messagebox sample the model returned exactly the three strings
(`user32.dll`, `Hello, from MSF!`, `MessageBox`, 39 bytes) in one 7.4 s /
5,363-token request, and the extracted payload still displayed the dialog.

Limits: the mode is capped at 64 KiB and is only a classifier; it does not
prove that the extraction is semantically safe.  Use
`--llm-verify messagebox` for the known sample, or your normal harness for
other payloads.  A range without a code reference is dropped, and a payload
with undecodable bytes plus an empty classification is rejected and retried.

### Options

| Option | Meaning |
|---|---|
| `--llm` | Enable LLM mode |
| `--llm-technique <eq\|nop\|bcf\|ibp>` | Technique to request |
| `--llm-shots <n>` | Number of worked examples in the prompt (default 1; 0 disables) |
| `--llm-data` / `--llm-classify-data` | LLM data classification instead of `-xd` |
| `--llm-data-json <file>` | Save classified ranges, xrefs and stats as JSON |
| `--llm-retries <n>` | Generation attempts (default 3) |
| `--llm-verify <static\|messagebox>` | Verification after assembly |
| `--llm-no-extract-data` | Skip the automatic `-xd` preprocessing |
| `--llm-min-similarity <float>` | Override the structural check floor |
| `--llm-dump-prompt <file>` | Save the full prompt |
| `--llm-dump-response <file>` | Save the last raw model response |
| `--llm-mock-response <file>` | Offline answer (testing; no API call) |
| `--llm-failed-output <file>` | Where to save the last rejected answer |
| `--llm-stats <file>` | Save token/time/cost statistics as JSON |

The data blob is appended by Zone after assembly and is checked byte for byte;
a model answer that touches it is rejected.  `RET_*` labels must stay
immediately after their `call`; an answer that separates them is rejected.

### Statistics, time and cost

Every `--llm` run ends with a statistics block.  It is printed **by default**;
`--llm-stats <file>` only adds a JSON copy, it is not required to see the
numbers.  A compact per-attempt line is also printed as soon as each API
answer arrives:

```
====================================================================
[llm] run statistics
  model:      deepseek-flash (DeepSeek-V4.1-Flash-1017)
  technique:  eq (x64)
  attempts:   1 (1 API call(s), 0 rejected)
  time:       1m 31.3s total (API 1m 31.3s, local 0.1s)
  attempt 1:  91.3s, ok, similarity 0.92
  tokens:     24,688 total = 3,545 input + 21,143 output
              input: 3,328 cache hit + 217 cache miss (93.9% hit)
              output: 21,143 (reasoning 20,061, 94.9%)
  throughput: 231.7 output tokens/s (API time)
  cost:       $0.012728 USD (off-peak)
              input $0.000043 (hit $0.000010, miss $0.000033) + output $0.012686
  payload:    359 code + 39 data bytes, 133 instructions
  validation: ok, similarity 0.92
====================================================================
```

`--llm-stats <file>` writes the same data as JSON (model, usage, per-call
timings, cost breakdown, payload stats, errors).  Costs are estimates from the
official DeepSeek price list (USD per 1M tokens):

| Model | Input cache hit (off-peak / peak) | Input cache miss (off-peak / peak) | Output (off-peak / peak) |
|---|---|---|---|
| `deepseek-flash` | $0.003 / $0.006 | $0.15 / $0.30 | $0.60 / $1.20 |
| `deepseek-v4-pro` | $0.022 / $0.044 | $0.66 / $1.32 | $1.98 / $3.96 |

Peak hours are 01:00-04:00 and 06:00-10:00 UTC, Monday-Friday; weekends are
off-peak.  Chinese public holidays are not modelled, so a holiday run is
classified by the weekday/hour rule only.  The model's reasoning tokens are
included in `completion_tokens` and are billed at the output rate, which is
why a reasoning-heavy run can cost more than its visible assembly suggests.
Rates can change; the table is a snapshot of
[the official pricing page](https://api-docs.deepseek.com/quick_start/pricing/).

Overrides:

| Variable | Meaning |
|---|---|
| `ZONE_LLM_PRICE_HIT` | USD per 1M cache-hit input tokens |
| `ZONE_LLM_PRICE_MISS` | USD per 1M cache-miss input tokens |
| `ZONE_LLM_PRICE_OUTPUT` | USD per 1M output tokens |
| `ZONE_LLM_EUR_RATE` | if set, also print an approximate EUR cost |

If the model is unknown and no override is set, the cost line is `n/a`.

### Limits and caveats

* The model output is sent to a third-party API.  Do not use this mode on
  payloads or secrets you are not allowed to share.
* Static validation catches structural mistakes, not every semantic one.  For
  a known payload, use `--llm-verify messagebox`; otherwise test the output
  with your normal harness.
* The model may refuse or produce invalid assembly; Zone reports the exact
  error, saves the last rejected answer, and exits non-zero.  It never writes a
  payload that failed validation.
* LLM mode currently supports one technique per run.  Combine techniques in
  the native engine, or run the LLM twice.
* `--llm` is not a replacement for the deterministic techniques: it is an
  experiment in model-written morphing with a strict assembler/validator around
  it.

Offline tests (no API key, no network) live in `test_llm_technique.py`:

```sh
python test_llm_technique.py
```

They cover canonicalisation round-trips on the real CPU, mocked `-eq`, `-nop`,
`-bcf` and `-ibp` answers, retry logic, the HTTP client, and rejection of
dropped instructions, extra `ret`s and missing getpc labels.

## Symbolic payload coverage

For a raw x86/x64 payload, install angr and run:

```sh
python -m pip install angr
python symbolic_payload_coverage.py original_pl/x64/windows_x64_messagebox.bin --arch x64 --output coverage.json
```

The script prints candidate data with virtual addresses, file offsets, and raw
hex bytes. Printable null-terminated runs are also decoded as ASCII or UTF-16LE.
The JSON report stores them in `data_candidates`. It distinguishes strings,
CFG-identified data, and bytes outside recovered CFG blocks. A forward
`call`/`pop` alone does not prove that skipped bytes are data: ordinary code
may execute when the callee returns. For a string overlapping CFG code, the
script requires the string to fill that whole call gap. All results remain
candidates, not proofs of data.

The same analysis is available as an importable function:

```python
from symbolic_payload_coverage import find_data_sections

sections = find_data_sections("payload.bin", arch="x64")
# Prints each string's start address, file offset, byte length, encoding, and text.
# [{"address": 0x400002, "offset": 2, "length": 6, "kind": "ascii"}, ...]
```

To also return the full string candidates, use `return_strings=True`:

```python
sections, string_candidates = find_data_sections(
    "original_pl/x64/windows_x64_messagebox.bin", arch="x64",
    base_address=0, return_strings=True,
)
for candidate in string_candidates:
    print(candidate["text"], candidate["offset_start"], candidate["size"])
```

Each string record contains `kind`, `offset_start`, `offset_end_exclusive`,
`address_start` (a hex string), `size`, `text`, `hex`, and `cfg_code_overlap`,
as in the CLI JSON report. `return_strings` is independent of `print_strings`;
without it, the return value remains the list of sections.

Pass raw bytes instead of a path if the payload is already in memory. The
default base address is 0x400000 and can be changed with base_address. Each
entry is a heuristic candidate; kind distinguishes strings, CFG data, and
bytes outside the recovered CFG.
String lengths include the NUL terminator. Pass `print_strings=False` for silent
library use. Both entry points print the input path (or an in-memory label),
byte size, SHA-256, load base, entry address, and exploration stop diagnostics.
The CLI JSON report also includes `payload_sha256`.
To compare library and CLI results, use the same input bytes, architecture,
base address, entry offset, and exploration limits. For a base below 0x10000,
`find_data_sections()` analyzes at an internal nonzero base and translates the
reported addresses back, because CFGFast can mistake small payload constants
for data pointers at a low base; the CLI does not rebase and warns instead.

Symbolic execution records instruction addresses. A second CFGFast pass starts
at code entries observed at runtime but missed by the first pass. The report
includes `cfg_observed_code_blocks`, `cfg_plausible_code_blocks`, and
`cfg_unobserved_code_block_addresses`; unvisited CFG blocks remain uncertain.
CFGFast can also mistake inline strings for instructions, so unexecuted string
bytes take precedence in the candidate list. `--scan-all` searches more of the
blob for code but can misclassify data. `--oppologist` can try Unicorn on
unsupported instructions, potentially concretizing symbolic values.

The default exploration stops after 10,000 state/block steps, 120 seconds, or
when more than 10,000 states are queued. Set an individual limit to `0` to
disable it. `coverage_status`, `stop_reason`, `pending_states`,
`unconstrained_states`, and `errors` show why coverage may be incomplete.
The script prints progress every five seconds (`--progress-interval`) and
limits each solver query to five seconds (`--solver-timeout-ms`).
Addresses marked `not_observed` are **not** proven unreachable: the analysis
uses a blank raw-payload environment and does not initialize OS structures or
external APIs. In particular, Windows shellcode that reads the PEB or calls
APIs may leave paths unexplored. The timeout is checked between symbolic steps.

## Data extraction (opt-in)

The symbolic analysis runs only when `--find-data` or `--extract-data` is given.
The same analysis can move the payload data to the end of the blob:

```sh
python pobf.py original_pl/x64/windows_x64_messagebox.bin --find-data
python pobf.py original_pl/x64/windows_x64_messagebox.bin --extract-data
python pobf.py original_pl/x64/windows_x64_messagebox.bin --extract-data -eq -nop -o out.bin
python pobf.py original_pl/x64/windows_x64_messagebox.bin --extract-data --eliminate-bad-instructions -bcf -o out.bin
```

`--find-data` (`-fd`) runs the symbolic exploration, prints the data ranges and
their xrefs, and exits without writing anything.

`--extract-data` (`-xd`) rewrites the payload:

- a `call $+N; pop reg` sequence that pushes a data address becomes
  `lea reg, [rip + disp]` plus NOP padding, keeping the payload length and every
  instruction address unchanged;
- the data bytes are appended after a 16-byte boundary;
- RIP-relative, absolute-memory, and `mov`/`push` immediate references are
  adjusted after the optional morphing (`-eq`, `-nop`, ...), because the final
  code length determines the displacement;
- a section with a reference that cannot be rewritten safely is left in place
  and reported.

`--extract-unknown` (`-xu`) also moves `outside_cfg` ranges, which are heuristic
and may be code. `--data-timeout <seconds>` sets the symbolic exploration
timeout (default 120). `--extract-data` can be combined with
`--position-independent-instr` (`-pii`): the indexed dispatcher shuffles the
instruction handler units (the entry stays first) and places the extracted data
after its instruction map; the `lea` displacements are finalized against that
layout. `-pii` also works without extraction, but `--extract-data` is
recommended because the linear sweep can miss the payload tail. A separate
`--instruction-permutation` (`-ip`) mode permutes single instructions with an
explicit successor `jmp`; it is **not** the PII dispatcher. Without
`--extract-data` the data analysis never modifies the payload.

`--eliminate-bad-instructions` (`-ebi`) expands `jrcxz`/`loop` short branches
into a 12-byte trampoline before morphing, so their ±127-byte relative limit is
no longer a problem. It is applied in both the normal and `--extract-data`
paths, and is compatible with `-eq`, `-nop`, and `-bcf` (an example that used to
hit the `DIFF > 120` restart). Each expanded branch adds 10 bytes. Without it,
the old restart/abort fallback may trigger.

The `je` inserted by `-bcf` is registered in the label table as well, so later
random insertions cannot invalidate its target. In a 10-run `ploader.exe` test,
`-xd -bcf -ebi` produced 10/10 payloads that displayed the message box; the
same test against the previous code produced 3/10.

The discovered data sections are cached by payload SHA-256 in `data_cache.json`
(override with `--data-cache <file>`). A second run with the same payload skips
the symbolic exploration and reuses the stored sections; xrefs are still
recomputed. `--refresh-data-cache` (`-rc`) forces a fresh search and replaces
the entry, `--no-data-cache` (`-nc`) disables the cache. The cache stores the
timeout used, but a hit reuses it even if `--data-timeout` changed; refresh to
re-run with new limits.

This is a size-preserving rewrite: the data disappears from the code area (it
is replaced by NOPs) and the output grows by the appended blob. Compacting the
code would renumber every instruction and is not attempted here.


# Zone: A Payload-Obfuscator with Metamorphic Engine

## 32-bit build (`pobf86.py`)

The 32-bit build now has the `-bcf` `je` label fix, `-ebi`
(`loop`/`loope`/`loopne`/`jecxz`/`jcxz` trampolines), the indexed and shuffled
`-pii` dispatcher, and the separate `-ip` single-instruction permutation. The
old `brain_mode` bug that always selected `write_strange_file()` has been
removed; a normal run now uses `write_file()`.

On the 32-bit messagebox, `-eq`, `-nop`, and `-bcf` now display the message box
(3/3 `-nop` and `-bcf`, 3/3 `-eq` in the `cdb` tests). The fixes that made this
work were:

- `pushf`/`popf` in Keystone 32 were being encoded as 16-bit (`66 9C`/`66 9D`)
  and unbalanced the stack; all generated code now uses `pushfd`/`popfd`;
- printable inline data ranges are marked and skipped by `-eq`/`-nop`/`-bcf`;
- `-nop` uses plain `nop` instructions, only after the last inline data block,
  and never between a call and its inline getpc data;
- `-bcf` only inserts bogus blocks after the last inline data block.

This is a conservative static heuristic, not a full x86 CFG classifier. `-pii`
and `-ip` still move the inline data and therefore remain **experimental** on
data-bearing 32-bit payloads; use `-xd` to move the data out first.

The dispatcher itself uses `pushad`/`popad` plus a saved-flags slot and `ret`,
so all general registers and flags are preserved; the earlier register-pressure
fallback to `ebx` is gone.

### 32-bit symbolic data layer (`-fd`, `-xd`)

`pobf86.py` now has the same data layer as `pobf.py`. The symbolic analyzer is
the same one (`symbolic_payload_coverage.py --arch x86`); what differs is the
32-bit reference model and the getpc rewrite:

- references are absolute 32-bit immediates and `[disp32]` memory operands
  (there is no RIP-relative addressing); a section is moved only if **every**
  reference to it is classified as supported (`getpc`, `abs` or `imm`), and a
  section with no verified reference is left in place;
- a `call` whose return address is the start of a data section and whose target
  is its end is a getpc site (classic `call $+5; pop`, late pop, or the 32-bit
  idiom that leaves the pushed string address on the stack as an API argument);
- when the analyzer classifies only the tail of an inline string (the linear
  sweep decodes its first bytes as code), the section is extended back to the
  call return address if the whole gap is printable. This is what keeps the
  32-bit messagebox caption (`MessageBox`, at `0xb4`) intact instead of letting
  the morphing shift the call return address and show a garbage title;
- at extraction the call is kept and only the inline data is replaced by NOPs;
  after the final layout the call becomes `jmp stub`, where the 5-byte stub
  `call consumer` is placed right before the moved data. The stub pushes the
  new data address and jumps to the original consumer, so no `lea rip` is
  needed and the payload stays position-independent.

Flags: `--find-data/-fd`, `--extract-data/-xd`, `--extract-unknown/-xu`,
`--data-timeout`, `--data-cache`, `--no-data-cache/-nc`,
`--refresh-data-cache/-rc`. Sections are cached by payload SHA-256, and the
xref scan is recomputed on every run. The old naive `call/pop` heuristic that
classified the whole resolver as data has been removed.

`-xd` was validated by execution with `ploader86.exe` on the 32-bit messagebox:
`-xd`, `-xd -eq`, `-xd -nop`, `-xd -ebi -bcf`, `-xd -ebi -nop -eq`,
`-xd -ip` and `-xd -pii` all still display the message box. On the reverse_tcp
family the analyzer finds no inline data (those payloads resolve APIs by hash),
so `-xd` is a no-op there.

## Overview

**Zone** is a PE-obfuscator equipped with a metamorphic engine, designed to evade static analysis. This project represents a significant personal achievement, likened to the most challenging "hello_world.exe" I've ever created.

## Introduction to Metamorphism

Metamorphism is a sophisticated technique used in software obfuscation, particularly for evading static analysis. Unlike simpler techniques, metamorphism modifies the executable at the assembly level while preserving its original functionality. This approach inserts a high level of randomness, making it extremely difficult to create a reliable signature for detection.

## Why Metamorphism?

Static analysis evasion techniques often fall short as they can be easily detected and signatured, especially in the case of crypters/packers and simple payload executors. Metamorphism addresses these limitations by ensuring every run of the engine generates a different version of the executable, with no detectable stubs left behind.

## The Journey

Creating a metamorphic engine/PE obfuscator is no small feat. This project has been the most challenging endeavor of my life, largely due to the lack of existing code to reference. The name ‘Zone’ is inspired by the film "Stalker" by Andrei Tarkovsky, reflecting a place where every path appears different but leads to the same destination.

## Code Morphing Techniques

Techniques are also usable together but some 'heavy' techniques would eventually break if used together (like don't Use PII with instruction block permutation)

### 1. Equal Code Substitution

This technique involves replacing certain instructions with other instructions that achieve the same result but in a different way. For example:
- `xor reg, reg` → `mov reg, 0`
- `sub reg, 0xVALUE` → `add reg, -0xVALUE`
- `mov REG, 0xVALUE` → `push VALUE; pop REG`

### 2. Random NOPs Insertion

Random instructions that do not affect the functionality of the program are inserted into the code. These include:
- `NOP`
- `SUB REG, 0x0`
- `ADD REG, 0x0`
- `MOV REG, REG`
- `LEA REG, [REG+0]`
- `PUSH REG` and `POP REG`
- Various other instructions that modify CPU flags, surrounded by `PUSHF` and `POPF` to preserve the flags' state.


### 3. Bogus Control Flow

This technique, involves creating fake conditions and blocks of code that will never be executed, confusing decompilers, malware analysts, and AVs.

### 4. Instruction Blocks Permutation

this feature will involve dividing instructions into blocks, adding jumps at the end of each block, and shuffling these blocks to create highly obfuscated code.

The block builder now keeps every instruction (the old version skipped the
last instruction and dropped the final block), keeps `-ebi` trampolines in one
block, and fixes the entry and final blocks so the last one cannot fall through
into a shuffled block. `-ibp -xd -ebi` on the messagebox sample was verified
10/10 with a `cdb` breakpoint on `user32!MessageBoxA`.

### 5. Position Independent Instruction

This technique is novel and is a ultra granular VM-like technique which allows to shuffle EVERY SINGLE INSTRUCTION. Please refer only to `pobf.py` and `pobf86.py` for this technique.

### 6. Assembly Wrapping (`-wrap`, x64 only)

Assembly wrapping hides the real instructions inside the immediate operand of a
benign `mov r64, imm64`. A linear or recursive disassembler keeps decoding the
`mov`, while the CPU is sent one byte *inside* the immediate.

```
entry:  push reg
        lea  reg, [rip + disp]      ; address of the first immediate
        xchg reg, [rsp]             ; push it, restore the register
        ret                         ; jump there (flags untouched)

0x00:   48 b8 <6 bytes of code> <EB dist> <junk>     ; static view: mov rax, imm64
0x0a:   49 b9 <6 bytes of code> <EB dist> <junk>     ; static view: mov rcx, imm64
```

Each 8-byte immediate holds up to six bytes of original code, a two-byte
`jmp short` and some junk. The jump lands on the immediate of the next
container, so execution chains through the payload while every byte stays
covered by a legal instruction. The entry stub is position independent and
restores the scratch register through the stack, so no register and no flag is
clobbered.

Some instructions do not fit (a `mov rax, 0x...` is ten bytes) or must keep a
byte-exact local layout (the `-ebi` trampolines, `loop`/`jrcxz`): they are
copied verbatim into "raw" blocks. Control flow through them is still glued
with the same short jumps, so semantics are preserved, but those bytes stay
visible to a disassembler. On the Metasploit x64 payloads about 95% of the
instructions fit in a container.

Options that shape the output (environment variables, useful for experiments):

| Variable | Default | Meaning |
|---|---|---|
| `ZONE_WRAP_SEED` | random | fixes chunking, wrapper registers and decoys |
| `ZONE_WRAP_GHOST` | `0.20` | probability of a decoy container between blocks |
| `ZONE_WRAP_JUNK` | `0.15` | probability of junk bytes between blocks |

Constraints:

- the payload must be fully disassembled: a skipped tail is refused;
- inline data (getpc `call`/`pop` strings) must be moved first with
  `--extract-data`; `-wrap` refuses with a clear error otherwise;
- `-wrap` implies `-ebi` (a `loop`/`jrcxz` a few bytes away would leave `rel8`
  range once its code is moved inside a container);
- it cannot be combined with `-pii` or `-ip`: those techniques already own the
  final layout;
- jump tables that store code addresses are not relocated;
- only `pobf.py` implements it (x86-64); the 32-bit build is unchanged.

The implementation lives in `asm_wrap.py` and is independent from the rest of
the engine, so it can be tested alone. Test entry points:

```sh
python test_asm_wrap.py          # chunking + real-CPU execution, 30 runs
python test_wrap_pipeline.py     # end-to-end through pobf.py, 40 cases
python test_wrap_messagebox.py   # MessageBox payload, 7 flag combinations x5
python check_messagebox.py <payload.bin>
```

Measured working rate on the x64 MessageBox payload with `--extract-data`:
5/5 dialogs for `-wrap`, `-wrap -eq`, `-wrap -nop`, `-wrap -bcf`,
`-wrap -eq -nop -bcf`, `-wrap -ibp` and `-wrap -eq -nop -bcf -ibp`
(average output 1.0-6.8 KB).


## Implementation Details

### Tools

This project utilizes two Python libraries:
- **Capstone**: A disassembler.  **ONLY DO pip install capstone==5.0.0.post1, last relase skip_data is broken**
- **Keystone**: An assembler.

# How Instructions are Patched



1. The program searches the .text section of the file and takes all the raw code.
2. It then disassembles all the code with Capstone and iterates through the instructions, creating a global list of a struct named `Instruction` (which I created). 

This is the struct:

# Example struct definition
```python
class Instruction:
    def __init__(self,new_instruction,old_instruction,original_instruction,prev_instruction,next_instruction):
        self.new_instruction = new_instruction
        self.old_instruction = old_instruction
        self.original_instruction = original_instruction
        self.prev_instruction = prev_instruction
        self.next_instruction = next_instruction
        self.address_history = []
```

Creating a global dictionary which will be `self.instr_dict[‘address’] = instruction`. It is done this way only because dictionaries are faster to use than lists.

3. Create a list of addresses which are used for jump-tables (`self.create_jmp_table()`).

I found a way to detect jump tables in this article: [Obfuscator Part 1](https://blog.es3n1n.eu/posts/obfuscator-pt-1/). Basically, jump tables are created by switch-case statements, and if I modify the addresses of my instruction, I also need to modify the addresses inside the jump tables.

4. Create a LABEL TABLE (`self.create_label_table()`).

This label table will be a list of tuples. I create the label table by iterating through all instructions and checking if they are some sort of JUMP or CALL. If they are a JUMP or a CALL, I create the tuple like this: 

```python
(JMP_INSTRUCTION, INSTRUCTION_WHERE_I_JUMP)
```

5. Do all the code modifications (equal code substitution, NOP insertions, etc.).

6. Patch the JUMP/CALL and all the references.

First, I patch all the jump/call instructions which typically do not have references outside of the .text section (`self.update_label_table()`). Then, I patch all the instructions (for example JMP/CALL/MOV) which have references to outside of the .text section. To know if they have such references, just search the disassembled string for something like `JMP QWORD PTR [RIP + 0x12345]`.

7. Patch the RELOC TABLE:

    A. Since all addresses changed and subroutine addresses changed, we need to patch the RELOC_TABLE, which is a structure used by the LOADER to modify hardcoded addresses when loading an .exe in memory.
    
    Check this to learn more about why we need to patch the RELOC TABLE: [PE Internals Part 7](https://0xrick.github.io/win-internals/pe7/).



# Increasing the .text Section

If the .text section has been heavily modified, we will need to increase its size because the padding between the .text section and the next section may not be sufficient.

Since this is not the core of the project, I will briefly explain how I increase the .text section.

## Steps to Increase the .text Section

1. **Patching the RELOC_TABLE**: 
   - Exactly the same as before, the RELOC_TABLE needs to be patched.

2. **Patching Headers**:
   - The following header values need to be patched:
     - `SizeOfCode`
     - `SizeOfImage`
     - Every `VirtualAddress` inside the `DATA_DIRECTORY`

   - Of the `.text` SECTION_HEADER:
     - `SizeOfRawData`
     - `Misc_VirtualSize`

   - Of every other section:
     - `VirtualAddress`
     - `PointerToRawData`

3. **Patching the ImportTable**:
   - Every entry of the ImportTable needs to be patched. The ImportTable contains every function imported from external libraries.

5. **Patching Every Reference Outside of .text**:
   - This is done exactly like in the main program using `self.adjust_out_of_text_references`.

6. **Adding Padding**:
   - Finally, add null bytes or `0x90` to the end of the .text section to reach the desired length.


9. **Writing modifications to the file**:

    A. Writing a new entry point.


# Usage
to use it just
1) compile you hello_world.c with **cl.exe hello_world.c**
2) run : **python3 zone.py hello_world.exe**
