import ctypes, ctypes.wintypes as wt, subprocess, sys, time
exe = r"C:\Users\ubu\Desktop\Zone\ploader.exe"
payload = sys.argv[1]
user32 = ctypes.WinDLL("user32", use_last_error=True)
cb_t = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
proc = subprocess.Popen([exe, payload])
time.sleep(1.5)
titles = []
def cb(hwnd, lparam):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == proc.pid:
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        titles.append((bool(user32.IsWindowVisible(hwnd)), buf.value))
    return True
user32.EnumWindows(cb_t(cb), 0)
print("pid", proc.pid, "alive", proc.poll() is None)
for v, t in titles: print(f"visible={v} title={t!r}")
proc.kill()
