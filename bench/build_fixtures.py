#!/usr/bin/env python3
"""Assemble the benign corpus, execute every original, and record the expected
result buffer before any transformation is tested.

Outputs:
    bench/fixtures/<arch>/<case>.bin
    bench/fixtures/cases.json
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from keystone import Ks, KS_ARCH_X86, KS_MODE_32, KS_MODE_64

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cases import CASES  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assemble(source: str, arch: str) -> bytes:
    ks = Ks(KS_ARCH_X86, KS_MODE_64 if arch == "x64" else KS_MODE_32)
    encoding, count = ks.asm(source, 0)
    if not encoding or count == 0:
        raise RuntimeError("keystone produced no code")
    return bytes(encoding)


def run(arch: str, payload: Path, output: Path) -> bytes | None:
    runner = HERE / "harness" / "bin" / f"runner_{arch}.exe"
    result = subprocess.run([str(runner), str(payload), str(output)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, timeout=20)
    if result.returncode != 0 or not output.exists():
        return None
    text = output.read_text().strip()
    if not text:
        return None
    return bytes(int(value, 16) for value in text.split(","))


def data_ranges(payload: bytes, case: dict) -> list[dict]:
    text = case.get("data_text")
    if not text:
        return []
    needle = text.encode("ascii") + b"\x00"
    offset = payload.find(needle)
    if offset < 0:
        return []
    return [{"offset": offset, "length": len(needle), "text": text}]


def check(buffer: bytes | None, expect: list[dict]) -> tuple[bool, str]:
    if buffer is None or len(buffer) != 256:
        return False, "runner crash or missing output"
    expected = bytearray(b"\xCC" * 256)
    for entry in expect:
        data = bytes.fromhex(entry["bytes"])
        offset = entry["offset"]
        if offset + len(data) > 256:
            return False, "expectation out of range"
        expected[offset:offset + len(data)] = data
    if buffer != expected:
        differences = [
            f"+{index:#04x}: {buffer[index]:02x}!={expected[index]:02x}"
            for index in range(256) if buffer[index] != expected[index]
        ]
        return False, "; ".join(differences[:8])
    return True, ""


def main() -> int:
    metadata = []
    failures = 0
    for arch, cases in CASES.items():
        directory = HERE / "fixtures" / arch
        directory.mkdir(parents=True, exist_ok=True)
        for case in cases:
            payload = assemble(case["source"], arch)
            path = directory / f"{case['name']}.bin"
            path.write_bytes(payload)
            output = HERE / "fixtures" / f"{arch}_{case['name']}_original.txt"
            buffer = run(arch, path, output)
            ok, detail = check(buffer, case["expect"])
            if not ok:
                failures += 1
                print(f"FAIL {arch}/{case['name']}: {detail}")
            else:
                print(f"ok   {arch}/{case['name']}: {len(payload)} bytes, "
                      f"buffer starts {buffer[:8].hex()}")
            metadata.append({
                "arch": arch,
                "name": case["name"],
                "kind": case["kind"],
                "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "size": len(payload),
                "sha256": sha256(payload),
                "expect": case["expect"],
                "requires_extract": case["requires_extract"],
                "data_ranges": data_ranges(payload, case),
                "notes": case["notes"],
                "original_ok": ok,
                "original_detail": detail,
                "original_buffer_sha256": sha256(buffer) if buffer else None,
            })

    (HERE / "fixtures" / "cases.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"cases: {len(metadata)}, original failures: {failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
