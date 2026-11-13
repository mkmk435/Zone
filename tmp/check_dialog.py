import ctypes, subprocess, time, sys
from ctypes import wintypes
user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetClassNameW = user32.GetClassNameW
PostMessageW = user32.PostMessageW
WM_CLOSE = 0x0010
def windows_of_pid(pid):
    found=[]
    def cb(hwnd, lparam):
        p=wintypes.DWORD(); GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value==pid:
            buf=ctypes.create_unicode_buffer(256); GetClassNameW(hwnd,buf,256)
            found.append((hwnd,buf.value))
        return True
    EnumWindows(EnumWindowsProc(cb),0)
    return found
payload=sys.argv[1]; loader=sys.argv[2]
proc=subprocess.Popen([loader,payload],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
deadline=time.time()+4; dlg=None
while time.time()<deadline:
    if proc.poll() is not None: break
    for hwnd,cls in windows_of_pid(proc.pid):
        if cls=="#32770": dlg=(hwnd,cls); break
    if dlg: break
    time.sleep(0.05)
if dlg:
    print("dialog shown", dlg)
    PostMessageW(dlg[0],WM_CLOSE,0,0)
    try: proc.wait(timeout=3)
    except subprocess.TimeoutExpired: proc.kill()
else:
    print("no dialog, rc", proc.poll())
    if proc.poll() is None: proc.kill()
