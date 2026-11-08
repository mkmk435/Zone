import ctypes, subprocess, sys, time, argparse
from ctypes import wintypes
from pathlib import Path

user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
IsWindowVisible = user32.IsWindowVisible
GetClassNameW = user32.GetClassNameW
PostMessageW = user32.PostMessageW
WM_CLOSE = 0x0010

def windows_of_pid(pid):
    found = []
    def cb(hwnd, lparam):
        p = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            GetClassNameW(hwnd, buf, 256)
            found.append((hwnd, buf.value))
        return True
    EnumWindows(EnumWindowsProc(cb), 0)
    return found

def test(path, tester="ploader.exe", wait=3.0):
    proc = subprocess.Popen([tester, str(path)])
    deadline = time.time() + wait
    dlg = None
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        ws = windows_of_pid(proc.pid)
        if ws:
            dlg = ws[0]
            break
        time.sleep(0.05)
    if dlg is None:
        if proc.poll() is None:
            proc.terminate()
        return False, "no-dialog"
    PostMessageW(dlg[0], WM_CLOSE, 0, 0)
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.terminate()
        return False, f"dialog-not-closed class={dlg[1]}"
    return proc.returncode == 0, f"dialog class={dlg[1]} rc={proc.returncode}"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--pattern", default="*messagebox*.bin")
    ap.add_argument("--report", default=None)
    args = ap.parse_args()
    files = sorted(Path(args.dir).glob(args.pattern))
    print(f"[INFO] {len(files)} files", flush=True)
    buf = []
    for n, f in enumerate(files, 1):
        ok, info = test(f)
        status = "OK" if ok else "FAIL"
        line = f"x64/{f.name},other,{status},{info}\n"
        print(line.strip(), flush=True)
        buf.append(line)
        if args.report and n % 10 == 0:
            with open(args.report, "a", encoding="utf-8") as rf:
                rf.writelines(buf); buf.clear()
    if args.report and buf:
        with open(args.report, "a", encoding="utf-8") as rf:
            rf.writelines(buf)
