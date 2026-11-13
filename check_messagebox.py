"""Execute a shellcode file with ploader.exe and detect its MessageBox."""

import ctypes
import ctypes.wintypes as wintypes
import subprocess
import sys
import time

user32 = ctypes.WinDLL("user32", use_last_error=True)
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND,
                                 wintypes.LPARAM)


def windows_for(pid):
    found = []

    def callback(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid:
            length = user32.GetWindowTextLengthW(hwnd)
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            class_name = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_name, 256)
            found.append((hwnd, class_name.value, title.value))
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return found


def check(payload, timeout=3.0):
    process = subprocess.Popen(["ploader.exe", payload],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    deadline = time.time() + timeout
    dialog = None
    while time.time() < deadline:
        if process.poll() is not None:
            break
        for hwnd, class_name, title in windows_for(process.pid):
            if class_name == "#32770":
                dialog = (hwnd, title)
                break
        if dialog:
            break
        time.sleep(0.05)

    if dialog:
        hwnd, title = dialog
        user32.PostMessageW(hwnd, 0x0010, 0, 0)      # WM_CLOSE
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        return f"dialog shown: {title!r}"

    code = process.poll()
    if code is None:
        process.kill()
        process.wait()
        return "process still running, no dialog found"
    return f"process exited with {code:#x}, no dialog"


if __name__ == "__main__":
    for path in sys.argv[1:]:
        print(f"{path}: {check(path)}")
