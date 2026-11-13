from capstone import *
from capstone.x86 import *
from keystone import *
import re

CODE = open("tmp/mb_xd.bin","rb").read()
code_len = 313
code = CODE[:code_len]
data = CODE[code_len:]
# data includes pad 7 bytes before blob at 0x140; final_data_blob starts at 0x140
blob_start = 0x140 - 0  # addresses are file offsets here
# Actually original code addresses 0..312, pad 313..319, blob 320..358
blob = CODE[320:]
print("code",len(code),"data",len(data),"blob",len(blob))

cs = Cs(CS_ARCH_X86, CS_MODE_64); cs.detail=True
insns = list(cs.disasm(code,0))
labels = set()
for ins in insns:
    for op in ins.operands:
        if op.type == X86_OP_IMM and ins.group(X86_GRP_JUMP) or (op.type == X86_OP_IMM and ins.mnemonic == "call"):
            if 0 <= op.imm < code_len:
                labels.add(op.imm)
# data refs
for ins in insns:
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            tgt = ins.address + ins.size + op.mem.disp
            if blob_start <= tgt < blob_start + len(blob):
                labels.add(("data", tgt - blob_start))
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
            tgt = op.mem.disp
            if blob_start <= tgt < blob_start + len(blob):
                labels.add(("data", tgt - blob_start))

def label_for_data(off): return f"DATA_{off:x}"

def fmt_ins(ins):
    global labels
    text = f"{ins.mnemonic} {ins.op_str}".strip()
    # direct branches/calls
    if ins.operands and ins.operands[0].type == X86_OP_IMM and (ins.group(X86_GRP_JUMP) or ins.mnemonic == "call"):
        tgt = ins.operands[0].imm
        if 0 <= tgt < code_len:
            # replace the last hex number in op_str
            newop = re.sub(r"0x[0-9a-fA-F]+", f"L_{tgt:x}", ins.op_str, count=1)
            return f"{ins.mnemonic} {newop}".strip()
    # memory refs
    if ins.operands:
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                tgt = ins.address + ins.size + op.mem.disp
                if blob_start <= tgt < blob_start + len(blob):
                    # rewrite [rip + 0xNN] to [rip + DATA_off]
                    newop = re.sub(r"\[rip \+ 0x[0-9a-fA-F]+\]", f"[rip + {label_for_data(tgt-blob_start)}]", ins.op_str)
                    return f"{ins.mnemonic} {newop}".strip()
            if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                tgt = op.mem.disp
                if blob_start <= tgt < blob_start + len(blob):
                    newop = re.sub(r"\[0x[0-9a-fA-F]+\]", f"[{label_for_data(tgt-blob_start)}]", ins.op_str)
                    return f"{ins.mnemonic} {newop}".strip()
    return text

lines=[]
for ins in insns:
    if ins.address in labels:
        lines.append(f"L_{ins.address:x}:")
    lines.append("    " + fmt_ins(ins))
for item in sorted([x for x in labels if isinstance(x, tuple)], key=lambda x: x[1]):
    off = item[1]
    lines.append(f"{label_for_data(off)}:")
    lines.append("    .byte " + ", ".join(f"0x{b:02x}" for b in blob[off:off+ (11 if off==0 else (17 if off==11 else 11))]))
src = "\n".join(lines)
print(src[:2000])
print("...")
open("tmp/canon.asm","w").write(src)
ks=Ks(KS_ARCH_X86,KS_MODE_64)
try:
    enc,cnt=ks.asm(src,0)
    out=bytes(enc)
    print("assembled",len(out),"orig code+blob",code_len+len(blob))
    # compare code area
    print("code identical", out[:code_len]==code)
    # find first diff
    for i,(a,b) in enumerate(zip(out,CODE)):
        if a!=b:
            print("first diff at",hex(i),hex(a),hex(b)); break
except Exception as e:
    print("ASM ERR", e)
