import csv, collections, re, sys

rows = list(csv.reader(open('new_test_report_5run.csv', encoding='utf-8', errors='replace')))
techs = ['eq_nop_pii', 'eq_nop_bcf', 'eq_nop_ibp', 'nop_eq', 'nop_pii', 'nop_bcf',
         'nop_ibp', 'eq_pii', 'eq_bcf', 'eq_ibp', 'nop', 'eq', 'pii', 'bcf', 'ibp',
         'xd_ebi', 'xd']
morph = set(techs[:15])


def split(name):
    stem = name[:-4]
    stem = re.sub(r'_\d+$', '', stem)
    for t in techs:
        if stem.endswith('_' + t):
            return stem[:-len(t) - 1], t
    return stem, '?'


data = []
for path, kind, res, reason in rows:
    arch, f = path.split('/', 1)
    pl, tech = split(f)
    data.append((arch, pl, tech, kind, res, reason))

print('rows', len(data))
x86 = [d for d in data if d[0] == 'x86']
print('x86 rows', len(x86), 'OK', sum(1 for d in x86 if d[4] == 'OK'))
print(collections.Counter((t, d[4]) for d in x86 for t in [d[2]] if t in ('xd', 'xd_ebi')))
print('\n--- x86 FAIL reasons (top) ---')
c = collections.Counter(r for a, _, _, _, res, r in data if a == 'x86' and res == 'FAIL')
for k, v in c.most_common(40):
    print(v, repr(k)[:220])

print('\n--- per technique (15 morph) x86 ---')
for t in techs[:15]:
    sub = [d for d in x86 if d[2] == t]
    ok = sum(1 for d in sub if d[4] == 'OK')
    print(f'{t:14s} {ok}/{len(sub)} = {100*ok/max(1,len(sub)):.1f}%')

print('\n--- per payload x86 (15 morph) ---')
for pl in sorted({d[1] for d in x86}):
    sub = [d for d in x86 if d[1] == pl and d[2] in morph]
    ok = sum(1 for d in sub if d[4] == 'OK')
    ctl = [d for d in x86 if d[1] == pl and d[2] in ('xd', 'xd_ebi')]
    cok = sum(1 for d in ctl if d[4] == 'OK')
    print(f'{pl:52s} morph {ok:3d}/{len(sub):3d} {100*ok/max(1,len(sub)):5.1f}%  ctl {cok}/{len(ctl)}')
