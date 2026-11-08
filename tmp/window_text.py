import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time

exe = r"C:\Users\ubu\Desktop\Zone\ploader86.exe"
payload = sys.argv[1]

user32 = ctypes.WinDLL("user32", use_last_error=True)
CB = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

proc = subprocess.Popen([exe, payload])
time.sleep(1.5)

top = []


def enum_top(hwnd, lparam):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == proc.pid and user32.IsWindowVisible(hwnd):
        top.append(hwnd)
    return True


user32.EnumWindows(CB(enum_top), 0)


def text_of(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


children = []


def enum_child(hwnd, lparam):
    buf = ctypes.create_unicode_buffer(512)
    user32.GetClassNameW(hwnd, buf, 512)
    children.append((buf.value, text_of(hwnd)))
    return True


for hwnd in top:
    print("dialog title:", repr(text_of(hwnd)))
    children.clear()
    user32.EnumChildWindows(hwnd, CB(enum_child), 0)
    for cls, text in children:
        print(f"  child {cls}: {text!r}")

proc.kill()
