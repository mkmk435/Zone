import csv, pathlib, collections

u = {}
for r in csv.DictReader(open('working_rate_unified.csv', encoding='utf-8')):
    if r['arch'] == 'x86' and r['is_low'] == 'yes':
        u[r['payload']] = r

# xd control outputs exist with _1.._5; compare first run to original
no_data = []
no_ebi = []
both = []
for pl, r in u.items():
    orig = pathlib.Path('original_pl/x86/%s.bin' % pl).read_bytes()
    xd = pathlib.Path('mutations_new_xd_ebi/x86/%s_xd_1.bin' % pl)
    xe = pathlib.Path('mutations_new_xd_ebi/x86/%s_xd_ebi_1.bin' % pl)
    d = xd.exists() and xd.read_bytes() == orig
    e = xe.exists() and xd.exists() and xe.read_bytes() == xd.read_bytes()
    if d:
        no_data.append(pl)
    if e:
        no_ebi.append(pl)
    if d and e:
        both.append(pl)

print('payloads:', len(u))
print('-xd byte-identical to original (no data extracted):', len(no_data))
for p in no_data:
    print('   ', p)
print('-ebi byte-identical to -xd (no loop/jcxz expanded):', len(no_ebi))
print('both no-ops:', len(both))
for p in both:
    print('   ', p)

tests = ok = 0
for pl in both:
    r = u[pl]
    ok += int(r['new_morph_ok'])
    tests += int(r['new_morph_total'])
print('both no-op payloads: new morph %d/%d = %.1f%%' % (ok, tests, 100 * ok / max(1, tests)))
print('share of the 2700-test matrix: %.1f%%' % (100 * tests / 2700))
