# ATTENTION
Right Now Zone is only somehow usable with small sized PIE payloads (both x64 and x86, especially tested with Metasploit framework payloads). so only look at the `pobf.py` and `pobf86.py`. Zone as a PE obfuscator is totally unreliable and only works/is tested against very small executables compiled by myself. Anything bigger makes Zone completely unusable. For PE implementation refer to `Zone.py`

## Disclaimer

This tool is designed and provided for educational, research, and authorized security assessment purposes only. 

Using this software against targets without prior mutual, explicit, and written consent is illegal. It is the end user's sole responsibility to comply with all applicable local, state, and international laws. 

The author(s) and contributor(s) assume no liability and are not responsible for any misuse, damage, or legal consequences caused by this program.

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
data-bearing 32-bit payloads; `-xd` is disabled with an explicit error.

The dispatcher itself uses `pushad`/`popad` plus a saved-flags slot and `ret`,
so all general registers and flags are preserved; the earlier register-pressure
fallback to `ebx` is gone. The symbolic data layer (`-fd`, `-xd`, cache,
`extract_data`) is **not yet ported** to 32-bit: it depends on the x64 analyzer
(`gs`/PEB, RIP-relative references). A naive 32-bit `call/pop` getpc heuristic
was tested and rejected: on the 32-bit messagebox it classified the whole
resolver (`call 0x1 ... pop ebp`) as inline data and moved it, corrupting the
payload. A proper 32-bit extractor needs CFG/reachability and absolute-reference
handling; it is a separate x86 analyzer task, not a copy of the x64 code.

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
