#!/usr/bin/env python3
"""Same as pltester.py but returns early when the payload process dies.

The original tester blocks for the full timeout even when ploader.exe has
already exited, which makes large regression runs much slower.  A process that
has exited cannot connect, so an early exit is equivalent to a timeout.
"""
import argparse
import socket
import subprocess
import time
import traceback
from pathlib import Path


def classify(name: str) -> str:
    lname = name.lower()
    if 'reverse' in lname:
        return 'reverse'
    if 'bind' in lname:
        return 'bind'
    return 'other'


def test_reverse(tester, bin_path, bind_ip, bind_port, timeout=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind_ip, bind_port))
    sock.listen(1)
    sock.settimeout(0.2)
    proc = subprocess.Popen([tester, str(bin_path)])
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            if proc.poll() is not None:
                return False
            try:
                conn, _ = sock.accept()
                conn.close()
                return True
            except socket.timeout:
                continue
        return False
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
        sock.close()


def test_bind(tester, bin_path, conn_ip, conn_port, timeout=5):
    proc = subprocess.Popen([tester, str(bin_path)])
    time.sleep(1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.3)
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            if proc.poll() is not None:
                return False
            try:
                sock.connect((conn_ip, conn_port))
                return True
            except Exception:
                time.sleep(0.1)
        return False
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
        sock.close()


def test_other(tester, bin_path, timeout=5):
    proc = subprocess.Popen([tester, str(bin_path)])
    try:
        proc.wait(timeout=timeout)
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tester64', default='ploader.exe')
    parser.add_argument('--tester86', default='ploader86.exe')
    parser.add_argument('--bins', default='mutations\\mutations')
    parser.add_argument('--bind-ip', default='0.0.0.0')
    parser.add_argument('--conn-ip', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=1234)
    parser.add_argument('--timeout', type=float, default=5.0)
    parser.add_argument('--batch-size', type=int, default=5)
    parser.add_argument('--report-file', default='test_report.txt')
    args = parser.parse_args()

    report_path = Path(args.report_file)
    report_buffer = []
    results = []
    count = 0

    already_tested = set()
    if report_path.exists():
        with report_path.open('r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',', 1)
                arch_file_part = parts[0]
                if '/' in arch_file_part:
                    arch, filename = arch_file_part.split('/', 1)
                    already_tested.add((arch, filename))

    for arch in ('x64', 'x86'):
        tester = args.tester64 if arch == 'x64' else args.tester86
        dir_path = Path(args.bins) / arch
        if not dir_path.exists():
            print(f"[!] Directory {dir_path} not found, skipping {arch}")
            continue
        for bin_file in sorted(dir_path.glob('*.bin')):
            if (arch, bin_file.name) in already_tested:
                continue
            kind = classify(bin_file.name)
            try:
                if kind == 'reverse':
                    ok = test_reverse(tester, bin_file, args.bind_ip, args.port, args.timeout)
                elif kind == 'bind':
                    ok = test_bind(tester, bin_file, args.conn_ip, args.port, args.timeout)
                else:
                    ok = test_other(tester, bin_file, args.timeout)
                status = 'OK' if ok else 'FAIL'
            except Exception:
                traceback.print_exc()
                status = 'ERROR'
            print(f"{arch}/{bin_file.name},{kind},{status},", flush=True)
            report_buffer.append(f"{arch}/{bin_file.name},{kind},{status},\n")
            count += 1
            if count % args.batch_size == 0:
                with report_path.open('a') as rf:
                    rf.writelines(report_buffer)
                report_buffer.clear()

    if report_buffer:
        with report_path.open('a') as rf:
            rf.writelines(report_buffer)
    print(f"Tests complete. Results written to {report_path.resolve()}")


if __name__ == '__main__':
    main()
