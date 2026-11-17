import csv, collections

u = {}
for r in csv.DictReader(open('working_rate_unified.csv', encoding='utf-8')):
    if r['arch'] == 'x86' and r['is_low'] == 'yes':
        u[r['payload']] = r


def fam(pl):
    for suffix, name in [
        ('_nonx_tcp', 'nonx'), ('_tcp_allports', 'allports'),
        ('_tcp_rc4_dns', 'tcp_rc4_dns'), ('_tcp_dns', 'tcp_dns'),
        ('_reverse_winhttp', 'winhttp'), ('_reverse_winhttps', 'winhttps'),
        ('_reverse_http', 'http'), ('_reverse_https', 'https'),
        ('_messagebox', 'messagebox'), ('_bind_tcp', 'bind_tcp'),
        ('_reverse_tcp', 'reverse_tcp')]:
        if pl.endswith(suffix):
            return name
    return 'other'


g = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
for pl, r in u.items():
    f = fam(pl)
    g[f][0] += int(r['old_original_ok']); g[f][1] += int(r['old_original_total'])
    g[f][2] += int(r['new_morph_ok']); g[f][3] += int(r['new_morph_total'])
    g[f][4] += 1
print(f'{"family":12s} {"n":>2s} {"old":>14s} {"new":>14s} {"delta":>7s}')
for f, (oo, ot, no, nt, n) in sorted(g.items(), key=lambda kv: -kv[1][2]):
    print(f'{f:12s} {n:2d} {oo:6d}/{ot:<7d} {no:6d}/{nt:<7d} {100*no/nt - 100*oo/ot:+7.1f}')

print('\n--- groups ---')
groups = {
    'plain+allports+msgbox': {'messagebox', 'allports', 'bind_tcp', 'reverse_tcp'},
    'dns families': {'tcp_dns', 'tcp_rc4_dns'},
    'nonx': {'nonx'},
    'winhttp': {'winhttp'},
    'http/https/winhttps': {'http', 'https', 'winhttps'},
}
for name, fams in groups.items():
    oo = sum(v[0] for f, v in g.items() if f in fams)
    ot = sum(v[1] for f, v in g.items() if f in fams)
    no = sum(v[2] for f, v in g.items() if f in fams)
    nt = sum(v[3] for f, v in g.items() if f in fams)
    n = sum(v[4] for f, v in g.items() if f in fams)
    print(f'{name:24s} payloads={n:2d} old {oo}/{ot} ({100*oo/ot:4.1f}%)  new {no}/{nt} ({100*no/nt:4.1f}%)  delta {100*no/nt-100*oo/ot:+5.1f} pp  new share {100*no/699:4.1f}%')

# excluding messagebox
oo = sum(int(r['old_original_ok']) for pl, r in u.items() if pl != 'windows_messagebox')
ot = sum(int(r['old_original_total']) for pl, r in u.items() if pl != 'windows_messagebox')
no = sum(int(r['new_morph_ok']) for pl, r in u.items() if pl != 'windows_messagebox')
nt = sum(int(r['new_morph_total']) for pl, r in u.items() if pl != 'windows_messagebox')
print(f'\nexcluding messagebox: old {oo}/{ot} ({100*oo/ot:.1f}%) new {no}/{nt} ({100*no/nt:.1f}%) delta {100*no/nt-100*oo/ot:+.1f} pp')
print(f'messagebox accounts for {68/2700*100:.1f} pp of the new 25.9% rate')
