from capstone import *
from capstone.x86 import *

cs = Cs(CS_ARCH_X86, CS_MODE_64)
cs.detail = True
code = bytes.fromhex(
    "488b0500000000"    # mov rax,[rip+0]
    "0f8400000000"      # je rel32
    "7400"              # je rel8
    "eb00"              # jmp rel8
    "e800000000"        # call rel32
    "488d0d0000" "00"   # lea rcx,[rip+0]
    "488b0425efbeadde"  # mov rax, qword ptr [0xdeadbeef] (abs)
    "488b8425efbeadde"  # mov rax,[rbp*1+disp]
    "ff2500000000"      # jmp qword ptr [rip+0]
    "e2fe"              # loop -2
    "e3fe"              # jrcxz -2
    "66e2fe"            # loop rel8 with 66 prefix
    "488b05ffffffff"    # mov rax,[rip-1]
    "4c8b0d00000000"    # mov r9,[rip+0]
    "48c7c000000000"    # mov rax, 0
    "8b0500000000"      # mov eax,[rip+0]
)
for i in cs.disasm(code, 0x1000):
    enc = i.encoding
    print("%08x %-22s %-40s size=%d grp=%s imm=%s enc(imm_off=%d,imm_sz=%d,disp_off=%d,disp_sz=%d,modrm_off=%d)"
          % (i.address, i.mnemonic, i.op_str, i.size,
             [g for g in i.groups], i.operands[0].imm if i.operands else None,
             enc.imm_offset, enc.imm_size, enc.disp_offset, enc.disp_size, enc.modrm_offset))
    for op in i.operands:
        if op.type == X86_OP_MEM:
            print("      mem: base=%s index=%s scale=%d disp=0x%x seg=%s size=%d"
                  % (i.reg_name(op.mem.base), i.reg_name(op.mem.index) if op.mem.index else '-',
                     op.mem.scale, op.mem.disp & 0xffffffffffffffff, i.reg_name(op.mem.segment), op.size))
        elif op.type == X86_OP_IMM:
            print("      imm: 0x%x size=%d" % (op.imm, op.size))
