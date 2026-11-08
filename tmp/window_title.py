import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time

exe = r"C:\Users\ubu\Desktop\Zone\ploader86.exe"
payload = sys.argv[1]

user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
IsWindowVisible = user32.IsWindowVisible

proc = subprocess.Popen([exe, payload])
time.sleep(1.5)

titles = []


def callback(hwnd, lparam):
    pid = wt.DWORD()
    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == proc.pid:
        length = GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        GetWindowTextW(hwnd, buf, length + 1)
        titles.append((bool(IsWindowVisible(hwnd)), buf.value))
    return True


EnumWindows(EnumWindowsProc(callback), 0)
print("pid", proc.pid, "alive", proc.poll() is None)
for visible, title in titles:
    print(f"visible={visible} title={title!r}")

proc.kill()
