from pathlib import Path

ports = {
    '1234': b'\xd2\x04', '4444': b'\x5c\x11', '8080': b'\x90\x1f',
    '443': b'\xbb\x01', '80': b'\x50\x00', '8443': b'\xfb\x20',
}
for arch in ('x86', 'x64'):
    print('==', arch)
    for p in sorted(Path('original_pl', arch).glob('*.bin')):
        b = p.read_bytes()
        hits = [k for k, v in ports.items() if v in b]
        if not hits and ('tcp' in p.name or 'nonx' in p.name):
            hits = ['none']
        print(f'{p.name:<52} {hits}')
