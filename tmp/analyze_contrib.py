import csv, collections

u = {}
for r in csv.DictReader(open('working_rate_unified.csv', encoding='utf-8')):
    if r['arch'] == 'x86' and r['is_low'] == 'yes':
        u[r['payload']] = r

# recompute per-technique old/new from raw test files is harder; use unified doc table
old = {  # technique: (ok, total) from WORKING_RATE_UNIFIED.md x86 old table
    'nop': (75, 360), 'eq': (216, 360), 'pii': (0, 299), 'bcf': (66, 360),
    'ibp': (51, 360), 'eq_nop_pii': (0, 339), 'eq_nop_bcf': (43, 360),
    'eq_nop_ibp': (27, 360), 'nop_eq': (73, 360), 'nop_pii': (0, 306),
    'nop_bcf': (62, 360), 'nop_ibp': (35, 360), 'eq_pii': (0, 291),
    'eq_bcf': (80, 360), 'eq_ibp': (44, 360),
}
new = {'nop': 40, 'eq': 104, 'pii': 45, 'bcf': 76, 'ibp': 43,
       'eq_nop_pii': 9, 'eq_nop_bcf': 56, 'eq_nop_ibp': 20, 'nop_eq': 40,
       'nop_pii': 9, 'nop_bcf': 55, 'nop_ibp': 31, 'eq_pii': 45,
       'eq_bcf': 79, 'eq_ibp': 47}
print('%-13s %8s %8s %8s %10s' % ('tech', 'old%', 'new%', 'delta pp', 'contrib pp'))
tot = 0.0
for t, (ok, n) in old.items():
    orate = 100 * ok / n
    nrate = 100 * new[t] / 180
    contrib = (new[t] - orate / 100 * 180) / 2700 * 100
    tot += contrib
    print('%-13s %8.1f %8.1f %+8.1f %10.2f' % (t, orate, nrate, nrate - orate, contrib))
print('sum contribution %.2f pp' % tot)

# x64 contrast
x = [r for r in csv.DictReader(open('working_rate_unified.csv', encoding='utf-8'))
     if r['arch'] == 'x64' and r['is_low'] == 'yes']
oo = sum(int(r['old_original_ok']) for r in x)
ot = sum(int(r['old_original_total']) for r in x)
no = sum(int(r['new_morph_ok']) for r in x)
nt = sum(int(r['new_morph_total']) for r in x)
print('\nx64 low: old %d/%d = %.1f%%  new %d/%d = %.1f%%' % (oo, ot, 100 * oo / ot, no, nt, 100 * no / nt))
for r in sorted(x, key=lambda r: int(r['new_morph_ok']) / max(1, int(r['new_morph_total']))):
    print('  %-48s %5.1f%% -> %5.1f%%' % (r['payload'], float(r['old_original_rate_pct'] or 0),
                                          float(r['new_morph_rate_pct'] or 0)))
