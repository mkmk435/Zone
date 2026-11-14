#!/usr/bin/env python3
"""Functional harness for raw Windows payloads (Zone campaign, 2026-11-13).

One observable per payload family:
  * messagebox                -> a #32770 dialog owned by the loader process
  * bind                      -> the loader listens on TCP 1234 and accepts
  * reverse / pingback        -> the loader opens a TCP connection to a local
                                 listener on 1234
  * anything else             -> the loader exits with code 0

The payloads are Metasploit raw shellcode; all network traffic stays on
127.0.0.1 and the process is killed after every check.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORT = 1234
LOADERS = {
    "x64": ROOT / "ploader.exe",
    "x86": ROOT / "ploader86.exe",
}

user32 = ctypes.WinDLL("user32", use_last_error=True)
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def kind_of(name: str) -> str:
    lowered = name.lower()
    if "messagebox" in lowered:
        return "messagebox"
    if "bind" in lowered or "pingback_bind" in lowered:
        return "bind"
    if "reverse" in lowered or "pingback" in lowered:
        return "reverse"
    return "other"


def _windows_for(pid: int):
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


def _kill(proc: subprocess.Popen) -> None:
    try:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
    except Exception:
        pass


def check(path: Path, arch: str, timeout: float = 5.0) -> tuple[bool, str, float]:
    """Return (ok, detail, elapsed_seconds)."""
    name = path.stem
    kind = kind_of(name)
    loader = str(LOADERS[arch])
    started = time.time()

    if kind == "messagebox":
        process = subprocess.Popen([loader, str(path)],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        dialog = None
        deadline = time.time() + timeout
        while time.time() < deadline:
            if process.poll() is not None:
                break
            for hwnd, class_name, title in _windows_for(process.pid):
                if class_name == "#32770":
                    dialog = (hwnd, title)
                    break
            if dialog:
                break
            time.sleep(0.05)
        if dialog:
            user32.PostMessageW(dialog[0], 0x0010, 0, 0)
            _kill(process)
            return True, f"dialog:{dialog[1]!r}", round(time.time() - started, 3)
        code = process.poll()
        _kill(process)
        return False, f"no-dialog rc={code}", round(time.time() - started, 3)

    if kind == "reverse":
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(("0.0.0.0", PORT))
            server.listen(1)
            server.settimeout(timeout)
            process = subprocess.Popen([loader, str(path)],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
            try:
                connection, peer = server.accept()
                connection.close()
                _kill(process)
                return True, f"connect:{peer[0]}:{peer[1]}", round(time.time() - started, 3)
            except (socket.timeout, OSError):
                _kill(process)
                return False, "no-connect", round(time.time() - started, 3)
        finally:
            server.close()

    if kind == "bind":
        process = subprocess.Popen([loader, str(path)],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if process.poll() is not None:
                break
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(0.4)
            try:
                client.connect(("127.0.0.1", PORT))
                client.close()
                _kill(process)
                return True, "bind-connect", round(time.time() - started, 3)
            except OSError:
                client.close()
                time.sleep(0.1)
        _kill(process)
        return False, "no-bind", round(time.time() - started, 3)

    # other: a clean exit is the only available observable
    process = subprocess.Popen([loader, str(path)],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    try:
        code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill(process)
        return False, "timeout", round(time.time() - started, 3)
    return code == 0, f"exit:{code}", round(time.time() - started, 3)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: harness.py <arch> <payload> [...]")
        raise SystemExit(2)
    arch = sys.argv[1]
    for item in sys.argv[2:]:
        ok, detail, elapsed = check(Path(item), arch)
        print(f"{'OK' if ok else 'FAIL'} {item} {detail} {elapsed}s")
