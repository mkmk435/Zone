import csv

u = {}
for r in csv.DictReader(open('working_rate_unified.csv', encoding='utf-8')):
    if r['arch'] == 'x86' and r['is_low'] == 'yes':
        u[r['payload']] = r

loop7 = ['windows_custom_reverse_tcp_allports', 'windows_meterpreter_reverse_tcp_allports',
         'windows_patchupmeterpreter_reverse_tcp_allports',
         'windows_shell_reverse_tcp_allports', 'windows_vncinject_reverse_tcp_allports',
         'windows_shell_bind_tcp', 'windows_shell_reverse_tcp']
data6 = ['windows_messagebox', 'windows_custom_reverse_https',
         'windows_custom_reverse_http', 'windows_vncinject_reverse_http',
         'windows_custom_reverse_winhttp', 'windows_meterpreter_reverse_winhttp']
assert set(loop7) | set(data6) <= set(u)
rest = [p for p in u if p not in loop7 and p not in data6]


def agg(names):
    oo = sum(int(u[p]['old_original_ok']) for p in names)
    ot = sum(int(u[p]['old_original_total']) for p in names)
    no = sum(int(u[p]['new_morph_ok']) for p in names)
    nt = sum(int(u[p]['new_morph_total']) for p in names)
    return oo, ot, no, nt


for label, names in [('loop7', loop7), ('data6', data6), ('rest23', rest), ('ALL', list(u))]:
    oo, ot, no, nt = agg(names)
    print('%-7s n=%2d old %4d/%4d = %5.1f%%   new %4d/%4d = %5.1f%%   delta %+5.1f pp' % (
        label, len(names), oo, ot, 100 * oo / ot, no, nt, 100 * no / nt, 100 * no / nt - 100 * oo / ot))

print()
oo, ot, no, nt = agg([p for p in data6 if p != 'windows_messagebox'])
print('data5 (no messagebox) old %d/%d = %.1f%% new %d/%d = %.1f%%' % (
    oo, ot, 100 * oo / ot, no, nt, 100 * no / nt))

print()
for p in loop7:
    r = u[p]
    print('%-48s old %5.1f%% new %5.1f%%' % (p, float(r['old_original_rate_pct']), float(r['new_morph_rate_pct'])))
