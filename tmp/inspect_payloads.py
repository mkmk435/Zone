from pathlib import Path
import re
for arch in ('x64','x86'):
    print('==', arch)
    for p in sorted(Path('original_pl', arch).glob('*.bin')):
        b = p.read_bytes()
        has1234 = b'\xd2\x04' in b
        ss = re.findall(rb'[ -~]{4,}', b)
        txt = [s.decode('latin1') for s in ss][:5]
        print(f'{p.name:<52} 1234={has1234} strings={txt}')
