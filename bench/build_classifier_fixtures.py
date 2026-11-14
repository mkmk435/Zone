#!/usr/bin/env python3
"""Assemble the classifier-only fixtures and record their ground truth."""
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
from classifier_cases import CASES  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assemble(source: str, arch: str) -> bytes:
    ks = Ks(KS_ARCH_X86, KS_MODE_64 if arch == "x64" else KS_MODE_32)
    encoding, _ = ks.asm(source, 0)
    if not encoding:
        raise RuntimeError("keystone produced no code")
    return bytes(encoding)


def run(arch: str, payload: Path, output: Path):
    runner = HERE / "harness" / "bin" / f"runner_{arch}.exe"
    result = subprocess.run([str(runner), str(payload), str(output)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, timeout=20)
    if result.returncode != 0 or not output.exists():
        return None
    text = output.read_text().strip()
    return bytes(int(value, 16) for value in text.split(",")) if text else None


def check(buffer, expect) -> tuple[bool, str]:
    if buffer is None or len(buffer) != 256:
        return False, "runner crash or missing output"
    expected = bytearray(b"\xCC" * 256)
    for entry in expect:
        data = bytes.fromhex(entry["bytes"])
        expected[entry["offset"]:entry["offset"] + len(data)] = data
    if buffer != expected:
        diff = [f"+{index:#04x}: {buffer[index]:02x}!={expected[index]:02x}"
                for index in range(256) if buffer[index] != expected[index]]
        return False, "; ".join(diff[:8])
    return True, ""


def main() -> int:
    metadata = []
    failures = 0
    for arch, cases in CASES.items():
        directory = HERE / "fixtures" / "classifier" / arch
        directory.mkdir(parents=True, exist_ok=True)
        for case in cases:
            payload = assemble(case["source"], arch)
            path = directory / f"{case['name']}.bin"
            path.write_bytes(payload)
            output = HERE / "fixtures" / "classifier" / \
                f"{arch}_{case['name']}_original.txt"
            buffer = run(arch, path, output)
            ok, detail = check(buffer, case["expect"])
            if not ok:
                failures += 1
                print(f"FAIL {arch}/{case['name']}: {detail}")
            ranges = []
            for text in case.get("data_text", []):
                needle = text.encode("ascii") + b"\x00"
                offset = payload.find(needle)
                if offset < 0:
                    raise RuntimeError(f"{arch}/{case['name']}: '{text}' "
                                       "not found")
                ranges.append({"offset": offset, "length": len(needle),
                               "text": text})
            for pattern in case.get("data_patterns", []):
                needle = bytes.fromhex(pattern["hex"])
                offset = payload.find(needle)
                if offset < 0:
                    raise RuntimeError(f"{arch}/{case['name']}: "
                                       f"{pattern['name']} not found")
                ranges.append({"offset": offset, "length": len(needle),
                               "name": pattern["name"]})
            ranges.sort(key=lambda item: item["offset"])
            print(f"ok   {arch}/{case['name']}: {len(payload)} bytes, "
                  f"data ranges {ranges}")
            metadata.append({
                "arch": arch, "name": case["name"], "kind": case["kind"],
                "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "size": len(payload), "sha256": sha256(payload),
                "expect": case["expect"],
                "data_ranges": ranges,
                "no_data": not ranges,
                "notes": case["notes"],
                "original_ok": ok,
            })
    (HERE / "fixtures" / "classifier_cases.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"cases: {len(metadata)}, failures: {failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
