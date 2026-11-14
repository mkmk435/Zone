```asm
_start:
mov ecx, dword ptr [esp + 4]
mov eax, 7
cmp eax, 7
jne L_16
jmp L_aaaa
L_16:
mov dword ptr [ecx], 0xdead
jmp L_1c
L_aaaa:
mov dword ptr [ecx], 0xaaaa
jmp L_1c
L_1c:
mov eax, 0xa
cmp eax, 0xa
jg L_2f
jmp L_1111
L_1111:
mov dword ptr [ecx + 4], 0x1111
jmp L_36
L_2f:
mov dword ptr [ecx + 4], 0x2222
jmp L_36
L_36:
ret
```