#!/usr/bin/env python3
"""Submit the new mutants to VirusTotal (quota-aware, two-phase).

Why two phases: the public API allows 500 requests/day and 240/hour.  Uploading
one file and polling its analysis costs 2-4 requests.  This script uploads all
files first (1 request each) and fetches the reports in a second pass (1 request
each), so 220 files fit in 440 requests.

Modes:
    upload   POST every missing file, save the analysis id
    report   GET /files/<sha256> for every uploaded file, save the last stats
    wait     upload + poll the analysis (small batches only)

Usage:
    python tmp/vt_submit.py --mode upload
    python tmp/vt_submit.py --mode report

The key is read from --keys (default api_keys.txt) or from VT_API_KEY.
Results are appended to tmp/vt_results.jsonl; the latest line per sha256 wins.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://www.virustotal.com/api/v3"


class RateLimiter:
    def __init__(self, interval: float):
        self.interval = interval
        self.last = 0.0

    def wait(self) -> None:
        delay = self.interval - (time.time() - self.last)
        if delay > 0:
            time.sleep(delay)
        self.last = time.time()


class Key:
    def __init__(self, value: str, interval: float):
        self.value = value
        self.limiter = RateLimiter(interval)
        self.remaining = None
        self.exhausted = False

    def _request(self, request: urllib.request.Request, retries: int = 3) -> dict:
        self.limiter.wait()
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")[:300]
            if error.code == 429 and retries > 0:
                print(f"[429] ...{self.value[-6:]} rate limited, sleep 90 s",
                      flush=True)
                time.sleep(90)
                return self._request(request, retries - 1)
            if error.code == 401:
                self.exhausted = True
            raise RuntimeError(f"HTTP {error.code}: {body}")
        except Exception:
            if retries > 0:
                time.sleep(30)
                return self._request(request, retries - 1)
            raise

    def quota(self) -> int:
        request = urllib.request.Request(
            f"{API}/users/{self.value}/overall_quotas",
            headers={"x-apikey": self.value})
        try:
            data = self._request(request)
            user = data["data"]["api_requests_daily"]["user"]
            self.remaining = user["allowed"] - user["used"]
        except Exception as error:
            print(f"[WARN] quota check ...{self.value[-6:]}: {error}", flush=True)
            self.remaining = 500
        return self.remaining

    def upload(self, path: Path) -> str:
        boundary = "----zone" + uuid.uuid4().hex
        payload = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        head = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; '
            f'filename="{path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode()
        tail = f"\r\n--{boundary}--\r\n".encode()
        request = urllib.request.Request(
            f"{API}/files", data=head + payload + tail, method="POST",
            headers={"x-apikey": self.value,
                     "Content-Type": f"multipart/form-data; boundary={boundary}"})
        data = self._request(request)
        return data["data"]["id"]

    def analysis(self, analysis_id: str) -> dict:
        request = urllib.request.Request(
            f"{API}/analyses/{analysis_id}",
            headers={"x-apikey": self.value})
        return self._request(request)

    def file_report(self, sha256: str) -> dict | None:
        request = urllib.request.Request(
            f"{API}/files/{sha256}", headers={"x-apikey": self.value})
        try:
            return self._request(request)
        except RuntimeError as error:
            if "HTTP 404" in str(error):
                return None
            raise


def load_latest(path: Path) -> dict:
    records = {}
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        records[record["sha256"]] = record
    return records


def manifest_entries(path: Path) -> list:
    entries = json.loads(path.read_text(encoding="utf-8"))
    unique, seen = [], set()
    for entry in entries:
        if entry["sha256"] in seen:
            continue
        seen.add(entry["sha256"])
        unique.append(entry)
    return unique


def resolve_keys(path: Path, interval: float) -> list:
    values = []
    if path.exists():
        values = [line.strip() for line in
                  path.read_text(encoding="utf-8").splitlines()
                  if line.strip() and not line.startswith("#")]
    if not values and os.environ.get("VT_API_KEY"):
        values = [value.strip() for value in
                  os.environ["VT_API_KEY"].replace("\n", ",").split(",")
                  if value.strip()]
    return [Key(value, interval) for value in values]


def pick_key(keys: list, position: int = 0) -> Key | None:
    for offset in range(len(keys)):
        item = keys[(position + offset) % len(keys)]
        if not item.exhausted and (item.remaining is None
                                   or item.remaining > 0):
            return item
    return None


def append(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def phase_upload(entries: list, records: dict, keys: list, out: Path,
                 interval: float, limit: int) -> None:
    todo = [entry for entry in entries
            if records.get(entry["sha256"], {}).get("status")
            not in ("uploaded", "completed")]
    if limit:
        todo = todo[:limit]
    print(f"[INFO] upload: {len(todo)} files", flush=True)
    for position, entry in enumerate(todo, 1):
        key = pick_key(keys, position)
        if key is None:
            print("[WARN] all keys exhausted", flush=True)
            break
        record = {"sha256": entry["sha256"], "file": entry["path"],
                  "technique": entry["technique"],
                  "date": time.strftime("%Y-%m-%dT%H:%M:%S")}
        try:
            analysis_id = key.upload(ROOT / entry["path"])
            record.update({"status": "uploaded", "analysis_id": analysis_id})
            if key.remaining is not None:
                key.remaining -= 1
            print(f"[{position}/{len(todo)}] uploaded {entry['path']}",
                  flush=True)
        except Exception as error:
            record.update({"status": "error", "error": str(error)})
            print(f"[{position}/{len(todo)}] ERROR {entry['path']}: {error}",
                  flush=True)
        append(out, record)


def phase_report(entries: list, records: dict, keys: list, out: Path,
                 limit: int, retry_pending: bool) -> None:
    todo = []
    for entry in entries:
        record = records.get(entry["sha256"], {})
        status = record.get("status")
        if status == "completed":
            continue
        if status == "uploaded" or (retry_pending and status == "pending"):
            todo.append(entry)
    if limit:
        todo = todo[:limit]
    print(f"[INFO] report: {len(todo)} files", flush=True)
    for position, entry in enumerate(todo, 1):
        key = pick_key(keys, position)
        if key is None:
            print("[WARN] all keys exhausted", flush=True)
            break
        record = {"sha256": entry["sha256"], "file": entry["path"],
                  "technique": entry["technique"],
                  "date": time.strftime("%Y-%m-%dT%H:%M:%S")}
        try:
            data = key.file_report(entry["sha256"])
            if data is None:
                record.update({"status": "pending",
                               "analysis_id": records[entry["sha256"]].get(
                                   "analysis_id")})
                print(f"[{position}/{len(todo)}] pending {entry['path']}",
                      flush=True)
            else:
                attributes = data["data"]["attributes"]
                stats = attributes.get("last_analysis_stats") or {}
                total = sum(stats.values()) if stats else 0
                record.update({
                    "status": "completed" if stats else "pending",
                    "analysis_id": records[entry["sha256"]].get("analysis_id"),
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "undetected": stats.get("undetected", 0),
                    "total": total,
                    "stats": stats,
                })
                if key.remaining is not None:
                    key.remaining -= 1
                print(f"[{position}/{len(todo)}] {entry['path']} -> "
                      f"{record['malicious']}/{total}", flush=True)
        except Exception as error:
            record.update({"status": "error", "error": str(error)})
            print(f"[{position}/{len(todo)}] ERROR {entry['path']}: {error}",
                  flush=True)
        append(out, record)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="vt_manifest.json")
    parser.add_argument("--keys", default="api_keys.txt")
    parser.add_argument("--out", default="tmp/vt_results.jsonl")
    parser.add_argument("--mode", choices=["upload", "report", "wait"],
                        default="upload")
    parser.add_argument("--interval", type=float, default=15.0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--retry-pending", action="store_true")
    args = parser.parse_args()

    entries = manifest_entries(ROOT / args.manifest)
    out = ROOT / args.out
    records = load_latest(out)
    keys = resolve_keys(ROOT / args.keys, args.interval)
    if not keys:
        print("[ERROR] no key: put one per line in api_keys.txt or set "
              "VT_API_KEY", flush=True)
        return 2
    for key in keys:
        print(f"[INFO] key ...{key.value[-6:]}: {key.quota()} left", flush=True)

    uploaded = sum(1 for record in records.values()
                   if record.get("status") in ("uploaded", "completed"))
    completed = sum(1 for record in records.values()
                    if record.get("status") == "completed")
    print(f"[INFO] {len(entries)} unique files, uploaded={uploaded}, "
          f"completed={completed}", flush=True)

    if args.mode == "upload":
        phase_upload(entries, records, keys, out, args.interval, args.limit)
    elif args.mode == "report":
        phase_report(entries, records, keys, out, args.limit,
                     args.retry_pending)
    else:
        phase_upload(entries, records, keys, out, args.interval, args.limit)
        phase_report(entries, load_latest(out), keys, out, args.limit,
                     args.retry_pending)

    records = load_latest(out)
    completed = sum(1 for record in records.values()
                    if record.get("status") == "completed")
    uploaded = sum(1 for record in records.values()
                   if record.get("status") in ("uploaded", "completed"))
    print(f"[DONE] uploaded={uploaded}/{len(entries)} "
          f"completed={completed}/{len(entries)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
