_start:
    cld
    and rsp, 0xfffffffffffffff0
    call L_d9
    push r9
    push r8
    push rdx
    xor rdx, rdx
    mov rdx, qword ptr gs:[rdx + 0x60]
    push rcx
    mov rdx, qword ptr [rdx + 0x18]
    push rsi
    mov rdx, qword ptr [rdx + 0x20]
L_24:
    xor r9, r9
    mov rsi, qword ptr [rdx + 0x50]
    movzx rcx, word ptr [rdx + 0x4a]
    xor rax, rax
    lodsb al, byte ptr [rsi]
    cmp al, 0x61
    jl L_3a
    sub al, 0x20
L_3a:
    ror r9d, 0xd
    add r9d, eax
    loop 0x30
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
    mov ecx, dword ptr [rax + 0x18]
    push rax
    mov r8d, dword ptr [rax + 0x20]
    add r8, rdx
L_75:
    jrcxz L_cd
    xor r9, r9
    dec rcx
    mov esi, dword ptr [r8 + rcx*4]
    add rsi, rdx
L_84:
    xor rax, rax
    lodsb al, byte ptr [rsi]
    ror r9d, 0xd
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
    mov r10d, 0x726774c
    call rbp
    mov r9, 0
    lea rdx, [rip + DATA_b]
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    lea r8, [rip + DATA_1c]
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    xor rcx, rcx
    mov r10d, 0x7568345
    call rbp
    xor rcx, rcx
    mov r10d, 0x56a2b5f0
    call rbp
DATA_0 = DATA + 0
DATA_b = DATA + 11
DATA_1c = DATA + 28
DATA:
    .byte 0x75, 0x73, 0x65, 0x72, 0x33, 0x32, 0x2e, 0x64, 0x6c, 0x6c, 0x00, 0x48, 0x65, 0x6c, 0x6c, 0x6f, 0x2c, 0x20, 0x66, 0x72, 0x6f, 0x6d, 0x20, 0x4d, 0x53, 0x46, 0x21, 0x00, 0x4d, 0x65, 0x73, 0x73, 0x61, 0x67, 0x65, 0x42, 0x6f, 0x78, 0x00
