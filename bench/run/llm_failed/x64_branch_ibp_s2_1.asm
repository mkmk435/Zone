```asm
_start:
    mov rax, 7
    cmp rax, 7
    jne L_16
    jmp block_B
L_16:
    mov qword ptr [rcx], 0xdead
    jmp block_D
block_B:
    mov qword ptr [rcx], 0xaaaa
    jmp L_1d
block_D:
L_1d:
    mov rdx, 0
    mov r8, 0xa
    cmp r8, 0xa
    jg L_3b
    jmp block_E
block_E:
    mov qword ptr [rcx + 8], 0x1111
    jmp L_43
L_3b:
    mov qword ptr [rcx + 8], 0x2222
    jmp block_G
block_G:
L_43:
    ret
```