from capstone import *
from capstone.x86 import *
from keystone import *
import re, sys

def canonicalize(code, blob, data_start, arch="x64"):
    mode = CS_MODE_64 if arch == "x64" else CS_MODE_32
    cs = Cs(CS_ARCH_X86, mode); cs.detail=True
    insns = list(cs.disasm(code, 0))
    covered = sum(i.size for i in insns)
    if covered != len(code):
        print("WARN coverage", covered, len(code))
    labels = set()
    data_labels = {}
    for ins in insns:
        if ins.operands and ins.operands[0].type == X86_OP_IMM:
            if ins.group(CS_GRP_JUMP) or ins.group(CS_GRP_CALL):
                tgt = ins.operands[0].imm
                if 0 <= tgt < len(code):
                    labels.add(tgt)
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                tgt = ins.address + ins.size + op.mem.disp
                if data_start <= tgt < data_start + len(blob):
                    data_labels[tgt - data_start] = None
            if arch == "x86" and op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                tgt = op.mem.disp
                if data_start <= tgt < data_start + len(blob):
                    data_labels[tgt - data_start] = None

    def data_label(off): return f"DATA_{off:x}"

    def fmt(ins):
        text = f"{ins.mnemonic} {ins.op_str}".strip()
        # direct branch / call
        if ins.operands and ins.operands[0].type == X86_OP_IMM:
            if ins.group(CS_GRP_JUMP) or ins.group(CS_GRP_CALL):
                tgt = ins.operands[0].imm
                if 0 <= tgt < len(code):
                    newop = re.sub(r"0x[0-9a-fA-F]+", f"L_{tgt:x}", ins.op_str, count=1)
                    return f"{ins.mnemonic} {newop}".strip()
        # data refs
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                tgt = ins.address + ins.size + op.mem.disp
                if data_start <= tgt < data_start + len(blob):
                    newop = re.sub(r"\[rip \+ 0x[0-9a-fA-F]+\]",
                                   f"[rip + {data_label(tgt-data_start)}]", ins.op_str)
                    return f"{ins.mnemonic} {newop}".strip()
            if arch == "x86" and op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                tgt = op.mem.disp
                if data_start <= tgt < data_start + len(blob):
                    newop = re.sub(r"\[0x[0-9a-fA-F]+\]",
                                   f"[{data_label(tgt-data_start)}]", ins.op_str)
                    return f"{ins.mnemonic} {newop}".strip()
        return text

    lines = ["_start:"]
    for ins in insns:
        if ins.address in labels:
            lines.append(f"L_{ins.address:x}:")
        lines.append("    " + fmt(ins))
    # append labels at the end of code, then the tool appends bytes
    for off in sorted(data_labels):
        lines.append(f"{data_label(off)} = DATA + {off}")
    return "\n".join(lines), labels, data_labels

# load mb_xd
raw = open("tmp/mb_xd.bin","rb").read()
code = raw[:313]; blob = raw[320:359]
src, labels, dl = canonicalize(code, blob, 0x140)
src += "\nDATA:\n    .byte " + ", ".join(f"0x{b:02x}" for b in blob) + "\n"
open("tmp/canon2.asm","w").write(src)
ks=Ks(KS_ARCH_X86,KS_MODE_64)
try:
    enc,_ = ks.asm(src,0)
    out=bytes(enc)
    open("tmp/canon2.bin","wb").write(out)
    print("assembled",len(out),"code",len(code),"blob",len(blob),"labels",len(labels),"data",len(dl))
    print("first bytes",out[:16].hex())
except Exception as e:
    print("ERR",e)
