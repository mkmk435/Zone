import sys

sys.path.insert(0, ".")
import zone_v2 as Z

z = Z.Zone(sys.argv[1], verbose=False)
table = int(sys.argv[2], 0)

print("=== istruzioni che riferiscono %#x ===" % table)
refs = []
for rva, insn in z.insns.items():
    for op in insn.operands:
        if op.type == 3 and op.mem.base == 41:
            target = insn.address + insn.size + op.mem.disp
            if table - 0x200 <= target <= table + 0x40:
                refs.append((rva, target))
        elif op.type == 2:  # IMM
            if op.imm & 0xFFFFFFFF == table:
                refs.append((rva, table))
for rva, target in refs:
    print("--- ref da %#x verso %#x" % (rva, target))
    order = sorted(z.insns)
    import bisect
    pos = bisect.bisect_left(order, rva)
    for j in range(max(0, pos - 6), min(len(order), pos + 10)):
        insn = z.insns[order[j]]
        mark = " <<<" if insn.address == rva else ""
        print("   %#x %-20s %s %s%s" % (insn.address, insn.bytes.hex(),
                                        insn.mnemonic, insn.op_str, mark))

print("=== jmp reg / jmp [mem] presenti ===")
count = 0
for rva, insn in z.insns.items():
    if insn.mnemonic == "jmp" and (insn.operands[0].type == 1 or insn.operands[0].type == 3):
        count += 1
        if count <= 12:
            print("   %#x %s %s" % (rva, insn.mnemonic, insn.op_str))
print("totale jmp indiretti:", count)
