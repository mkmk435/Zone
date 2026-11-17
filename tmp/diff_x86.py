import pathlib


def common_prefix(a, b):
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return n


def common_suffix(a, b):
    n = 0
    while n < min(len(a), len(b)) and a[-1 - n] == b[-1 - n]:
        n += 1
    return n


cases = ['windows_shell_reverse_nonx_tcp', 'windows_shell_reverse_tcp_dns',
         'windows_custom_reverse_tcp_rc4_dns', 'windows_custom_reverse_tcp_allports',
         'windows_messagebox', 'windows_custom_reverse_http']
for n in cases:
    orig = pathlib.Path('original_pl/x86/' + n + '.bin').read_bytes()
    print('==', n, 'orig', len(orig))
    for tech in ['xd', 'xd_ebi', 'nop', 'eq', 'bcf', 'ibp', 'pii']:
        p = pathlib.Path('mutations_new_xd_ebi/x86/%s_%s_1.bin' % (n, tech))
        if not p.exists():
            continue
        b = p.read_bytes()
        cp = common_prefix(orig, b)
        cs = common_suffix(orig, b)
        # where does the divergence start, in original vs new
        print('  %-7s size=%4d (+%4d) prefix=%3d suffix=%3d first-diff orig=%#x new=%#x' % (
            tech, len(b), len(b) - len(orig), cp, cs, cp, cp))
