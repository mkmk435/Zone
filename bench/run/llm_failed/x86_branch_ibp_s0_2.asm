```asm
_start:
    mov ecx, dword ptr [esp + 4]
    mov eax, 7
    cmp eax, 7
    jne L_16
    jmp block_1
L_16:
    mov dword ptr [ecx], 0xdead
    jmp L_1c
block_1:
    mov dword ptr [ecx], 0xaaaa
    jmp L_1c
L_1c:
    mov eax, 0xa
    cmp eax, 0xa
    jg L_2f
    jmp block_2
block_2:
    mov dword ptr [ecx + 4], 0x1111
    jmp L_36
L_2f:
    mov dword ptr [ecx + 4], 0x2222
    jmp L_36
L_36:
    ret
```