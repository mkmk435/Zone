#!/usr/bin/env python3
"""Fast payload working-rate tester for x64 and x86 raw shellcode.

Handles reverse (listener), bind (connect), and messagebox (window) payloads.
Each test runs in a Windows Job Object so the whole child tree is killed.
Results are appended as `arch/filename,kind,STATUS,detail` lines, compatible
with the historical test_report.txt format.
"""
import argparse
import ctypes
import csv
import os
import socket
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

PORT = 1234
CREATE_NO_WINDOW = 0x08000000
WM_CLOSE = 0x0010

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)

kernel32.CreateJobObjectW.restype = wintypes.HANDLE
kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
kernel32.SetInformationJobObject.restype = wintypes.BOOL
kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                             wintypes.LPVOID, wintypes.DWORD]
kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.restype = wintypes.BOOL
user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND,
                                            ctypes.POINTER(wintypes.DWORD)]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetClassNameW.restype = ctypes.c_int
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.PostMessageW.restype = wintypes.BOOL
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
                                wintypes.WPARAM, wintypes.LPARAM]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JobObjectExtendedLimitInformation = 9


class Guard:
    """Owns the child process and a kill-on-close job object."""

    def __init__(self):
        self.job = kernel32.CreateJobObjectW(None, None)
        self.ok = False
        if self.job:
            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            self.ok = bool(kernel32.SetInformationJobObject(
                self.job, JobObjectExtendedLimitInformation,
                ctypes.byref(info), ctypes.sizeof(info)))
        self.proc = None

    def launch(self, tester, payload):
        self.proc = subprocess.Popen(
            [str(tester), str(payload)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )
        if self.job:
            kernel32.AssignProcessToJobObject(self.job, int(self.proc._handle))
        return self.proc

    def close(self):
        if self.proc is not None and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        # closing the job kills any surviving descendants
        if self.job:
            kernel32.CloseHandle(self.job)
            self.job = None
        if self.proc is not None:
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    self.proc.kill()
                except Exception:
                    pass
                try:
                    self.proc.wait(timeout=1)
                except Exception:
                    pass


def classify(name):
    n = name.lower()
    if "messagebox" in n:
        return "other"
    if "reverse" in n:
        return "reverse"
    if "bind" in n:
        return "bind"
    return "other"


def open_listener(port=PORT, timeout=3.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
            s.listen(1)
            s.settimeout(0.1)
            return s
        except OSError:
            s.close()
            time.sleep(0.1)
    return None


def windows_of_pid(pid):
    found = []

    @WNDENUMPROC
    def cb(hwnd, lparam):
        p = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, buf, 256)
            found.append((hwnd, buf.value))
        return True

    user32.EnumWindows(cb, 0)
    return found


def test_reverse(tester, payload, timeout):
    listener = open_listener()
    if listener is None:
        return False, "port-busy"
    guard = Guard()
    try:
        proc = guard.launch(tester, payload)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if proc.poll() is not None:
                return False, f"exited rc={proc.returncode}"
            try:
                conn, _ = listener.accept()
                conn.close()
                return True, ""
            except socket.timeout:
                continue
            except OSError:
                return False, "listener-error"
        return False, "timeout"
    finally:
        guard.close()
        listener.close()


def test_bind(tester, payload, timeout):
    guard = Guard()
    try:
        proc = guard.launch(tester, payload)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if proc.poll() is not None:
                return False, f"exited rc={proc.returncode}"
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            try:
                s.connect(("127.0.0.1", PORT))
                return True, ""
            except OSError:
                pass
            finally:
                s.close()
            time.sleep(0.05)
        return False, "timeout"
    finally:
        guard.close()


def test_messagebox(tester, payload, timeout):
    guard = Guard()
    try:
        proc = guard.launch(tester, payload)
        deadline = time.time() + timeout
        dlg = None
        while time.time() < deadline:
            if proc.poll() is not None:
                return False, f"exited rc={proc.returncode}"
            ws = windows_of_pid(proc.pid)
            if ws:
                dlg = ws[0]
                break
            time.sleep(0.05)
        if dlg is None:
            return False, "no-dialog"
        user32.PostMessageW(dlg[0], WM_CLOSE, 0, 0)
        closed = False
        try:
            proc.wait(timeout=2.0)
            closed = True
        except subprocess.TimeoutExpired:
            pass
        return True, f"dialog class={dlg[1]} closed={closed} rc={proc.returncode}"
    finally:
        guard.close()


def test_other(tester, payload, timeout):
    guard = Guard()
    try:
        proc = guard.launch(tester, payload)
        try:
            proc.wait(timeout=timeout)
            return proc.returncode == 0, f"rc={proc.returncode}"
        except subprocess.TimeoutExpired:
            return False, "timeout"
    finally:
        guard.close()


def run_one(tester, payload, kind, timeout):
    if kind == "reverse":
        return test_reverse(tester, payload, timeout)
    if kind == "bind":
        return test_bind(tester, payload, timeout)
    if "messagebox" in payload.name.lower():
        return test_messagebox(tester, payload, timeout)
    return test_other(tester, payload, timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bins", default="mutations_new_xd_ebi")
    ap.add_argument("--report", default="new_test_report.csv")
    ap.add_argument("--tester64", default="ploader.exe")
    ap.add_argument("--tester86", default="ploader86.exe")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--arch", choices=["x64", "x86", "both"], default="both")
    ap.add_argument("--glob", default="*.bin")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-resume", action="store_true")
    args = ap.parse_args()

    report = Path(args.report)
    done = set()
    if report.exists() and not args.no_resume:
        with report.open("r", encoding="utf-8", errors="replace") as f:
            for row in csv.reader(f):
                if row and "/" in row[0]:
                    done.add(tuple(row[0].split("/", 1)))
    print(f"[INFO] resuming: {len(done)} already tested", flush=True)

    arches = ["x64", "x86"] if args.arch == "both" else [args.arch]
    files = []
    for arch in arches:
        d = Path(args.bins) / arch
        if not d.exists():
            print(f"[!] missing {d}")
            continue
        for f in sorted(d.glob(args.glob)):
            files.append((arch, f))
    if args.limit:
        files = files[:args.limit]
    print(f"[INFO] {len(files)} files to test", flush=True)

    n_ok = n_fail = n_skip = 0
    t0 = time.time()
    for i, (arch, f) in enumerate(files, 1):
        if (arch, f.name) in done:
            n_skip += 1
            continue
        tester = args.tester64 if arch == "x64" else args.tester86
        kind = classify(f.name)
        try:
            ok, detail = run_one(Path(tester), f, kind, args.timeout)
            status = "OK" if ok else "FAIL"
        except Exception as e:
            status, detail = "ERROR", f"{type(e).__name__}: {e}"
        if status == "OK":
            n_ok += 1
        else:
            n_fail += 1
        line = f"{arch}/{f.name},{kind},{status},{detail}\n"
        with report.open("a", encoding="utf-8", newline="") as rf:
            rf.write(line)
        if i % 25 == 0 or i == len(files):
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed else 0
            eta = (len(files) - i) / rate / 60 if rate else 0
            print(f"[{i}/{len(files)}] ok={n_ok} fail={n_fail} "
                  f"skip={n_skip} {rate:.1f}/s ETA {eta:.1f} min", flush=True)
    print(f"[DONE] ok={n_ok} fail={n_fail} skip={n_skip} "
          f"elapsed={time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
