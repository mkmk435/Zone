import csv, collections, re

# --- per-payload old vs new ---
u = {}
for r in csv.DictReader(open('working_rate_unified.csv', encoding='utf-8')):
    if r['arch'] != 'x86' or r['is_low'] != 'yes':
        continue
    u[r['payload']] = r

print('x86 low payloads in unified:', len(u))
tot_old_ok = tot_old_n = tot_new_ok = tot_new_n = 0
rows = []
for pl, r in u.items():
    ook, ot = int(r['old_original_ok']), int(r['old_original_total'])
    nok, nt = int(r['new_morph_ok']), int(r['new_morph_total'])
    if nt == 0:
        continue
    tot_old_ok += ook; tot_old_n += ot; tot_new_ok += nok; tot_new_n += nt
    rows.append((pl, ook / max(ot, 1) * 100, nok / max(nt, 1) * 100, ook, ot, nok, nt))
print(f'totals old {tot_old_ok}/{tot_old_n} = {100*tot_old_ok/tot_old_n:.1f}%   new {tot_new_ok}/{tot_new_n} = {100*tot_new_ok/tot_new_n:.1f}%')
print()
print(f'{"payload":52s} {"old%":>6s} {"new%":>6s} {"delta":>7s}')
for pl, o, n, ook, ot, nok, nt in sorted(rows, key=lambda x: x[2] - x[1], reverse=True):
    print(f'{pl:52s} {o:6.1f} {n:6.1f} {n-o:+7.1f}   ({ook}/{ot} -> {nok}/{nt})')

# --- failure modes per family, x86 morph configs only ---
techs = ['eq_nop_pii', 'eq_nop_bcf', 'eq_nop_ibp', 'nop_eq', 'nop_pii', 'nop_bcf',
         'nop_ibp', 'eq_pii', 'eq_bcf', 'eq_ibp', 'nop', 'eq', 'pii', 'bcf', 'ibp']
morph = set(techs)


def split(name):
    stem = re.sub(r'_\d+$', '', name[:-4])
    for t in techs + ['xd_ebi', 'xd']:
        if stem.endswith('_' + t):
            return stem[:-len(t) - 1], t
    return stem, '?'


def fam(pl):
    for suffix, name in [
        ('_nonx_tcp', 'nonx'), ('_tcp_allports', 'allports'),
        ('_tcp_rc4_dns', 'tcp_rc4_dns'), ('_tcp_dns', 'tcp_dns'),
        ('_reverse_winhttp', 'winhttp'), ('_reverse_winhttps', 'winhttps'),
        ('_reverse_http', 'http'), ('_reverse_https', 'https'),
        ('_bind_tcp', 'bind_tcp'), ('_reverse_tcp', 'reverse_tcp'),
        ('_messagebox', 'messagebox')]:
        if pl.endswith(suffix):
            return name
    return 'other'


def rc(reason):
    m = re.search(r'rc=(\d+)', reason)
    if m:
        v = int(m.group(1))
        return {3221225477: 'AV 0xC0000005', 3221225725: 'stack 0xC00000FD',
                3221225781: 'DLL? 0xC0000135', 0: 'exit rc=0'}.get(v, f'rc={v}')
    if reason.startswith('timeout'):
        return 'timeout'
    return reason[:30] or 'ok?'


rows2 = list(csv.reader(open('new_test_report_5run.csv', encoding='utf-8', errors='replace')))
per = collections.defaultdict(collections.Counter)
for path, kind, res, reason in rows2:
    arch, f = path.split('/', 1)
    if arch != 'x86':
        continue
    pl, t = split(f)
    if t not in morph:
        continue
    per[fam(pl)][rc(reason) if res == 'FAIL' else 'OK'] += 1
print('\n--- x86 morph outcomes by family ---')
for k, c in sorted(per.items(), key=lambda kv: -sum(kv[1].values())):
    n = sum(c.values())
    print(f'{k:12s} n={n:4d}  ' + '  '.join(f'{kk}={vv}' for kk, vv in c.most_common()))
