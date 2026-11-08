import glob, os
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

names = [
    "windows_x64_custom_reverse_https",
    "windows_x64_custom_reverse_winhttp",
    "windows_x64_custom_reverse_winhttps",
    "windows_x64_meterpreter_reverse_http",
    "windows_x64_meterpreter_reverse_https",
    "windows_x64_meterpreter_reverse_winhttp",
    "windows_x64_vncinject_reverse_http",
    "windows_x64_vncinject_reverse_winhttp",
    "windows_x64_vncinject_reverse_winhttps",
    "windows_x64_meterpreter_reverse_winhttps",
    "windows_x64_vncinject_reverse_https",
    "windows_x64_messagebox",
    "windows_x64_custom_reverse_http",
]

for n in names:
    p = f"original_pl/x64/{n}.bin"
    data = open(p, "rb").read()
    cs = Cs(CS_ARCH_X86, CS_MODE_64)
    cs.skipdata = True
    cov = 0
    count = 0
    for ins in cs.disasm(data, 0):
        cov += len(ins.bytes)
        count += 1
    print(f"{n:<45} {cov:5d}/{len(data):<5d} {cov/len(data)*100:5.1f}%  insns={count}")
