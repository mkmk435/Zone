import sys, subprocess, time, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
from pobf import Zone
from llm_payload import from_zone, assemble, validate
user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetClassNameW = user32.GetClassNameW
PostMessageW = user32.PostMessageW
def has_dialog(pid):
    found=[]
    def cb(hwnd,lparam):
        p=wintypes.DWORD(); GetWindowThreadProcessId(hwnd,ctypes.byref(p))
        if p.value==pid:
            buf=ctypes.create_unicode_buffer(256); GetClassNameW(hwnd,buf,256)
            if buf.value=="#32770": found.append(hwnd)
        return True
    EnumWindows(EnumWindowsProc(cb),0); return found
def check(path):
    proc=subprocess.Popen(["ploader.exe",path],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    deadline=time.time()+2
    dlg=None
    while time.time()<deadline:
        if proc.poll() is not None: break
        d=has_dialog(proc.pid)
        if d: dlg=d[0]; break
        time.sleep(0.03)
    if dlg:
        PostMessageW(dlg,0x10,0,0)
        try: proc.wait(timeout=2)
        except: proc.kill()
        return True
    if proc.poll() is None: proc.kill()
    return False

z = Zone(r"C:\Users\ubu\Desktop\Zone\original_pl\x64\windows_x64_messagebox.bin")
sections, xrefs = z.analyze_data(timeout=30, print_strings=False, cache_path="data_cache.json", use_cache=True)
z.extract_data(sections, xrefs); z.finalize_data_refs()
cp = from_zone(z, "x64")
lines = cp.source.splitlines()
# candidate insertion points: before instruction lines, excluding line after call / RET labels
points=[]
for i,line in enumerate(lines):
    s=line.strip()
    if not s or s.startswith(";") or s.endswith(":"): continue
    prev=lines[i-1].strip() if i else ""
    if prev.startswith("RET_") or prev.lower().startswith("call"):
        continue
    points.append(i)
print("points",len(points))
for n,p in enumerate(points):
    trial=lines[:p]+["    nop"]+lines[p:]
    try:
        asm=assemble("\n".join(trial), cp)
    except Exception as e:
        print(n,p,"ASM ERR",e); continue
    path=f"tmp/nop_{n}.bin"
    open(path,"wb").write(asm.payload)
    ok=check(path)
    # find instruction address at p
    print(n, "line", p, "addr", lines[p].strip()[:40], "->", "OK" if ok else "CRASH")
