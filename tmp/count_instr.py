import capstone, pathlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

print('capstone', capstone.__version__)
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
names = ['windows_shell_reverse_nonx_tcp', 'windows_shell_reverse_tcp_dns',
         'windows_custom_reverse_tcp_rc4_dns', 'windows_custom_reverse_tcp_allports',
         'windows_shell_reverse_tcp', 'windows_messagebox', 'windows_custom_reverse_http',
         'windows_custom_reverse_winhttp']
for n in names:
    b = pathlib.Path('original_pl/x86/' + n + '.bin').read_bytes()
    c = {}
    total = 0
    for i in md.disasm(b, 0):
        c[i.mnemonic] = c.get(i.mnemonic, 0) + 1
        total += i.size
    loops = sum(v for k, v in c.items() if k.startswith('loop') or k in ('jecxz', 'jcxz'))
    jcc = sum(v for k, v in c.items() if k.startswith('j') and k not in ('jmp', 'jecxz', 'jcxz'))
    print('%-40s size=%4d sweep=%4d loop/jcxz=%d call=%d pop=%d push=%d jmp=%d jcc=%d' % (
        n, len(b), total, loops, c.get('call', 0), c.get('pop', 0), c.get('push', 0),
        c.get('jmp', 0), jcc))
