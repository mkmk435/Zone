#!/usr/bin/env python3
"""Integrity and coherence audit of the VirusTotal artefacts already on disk.

No submission is performed.  The audit distinguishes:
  * completed scan with zero detections;
  * completed scan with detections;
  * analysis incomplete / pending;
  * result missing or artefact unverifiable.

Inputs (2025 campaign):
  results.json, results_original.json, results_sgn.json
Inputs (2026 campaign):
  vt_manifest.json, vt_originals.json, tmp/vt_results.jsonl,
  tmp/vt_results_original.jsonl

Outputs:
  bench/results/vt_audit.json
  bench/VT_AUDIT.md
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_date(value):
    if not isinstance(value, str) or not DATE_RE.match(value):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def build_index(directories) -> dict:
    index = {}
    for directory in directories:
        for path in directory.rglob("*.bin"):
            arch = "x64" if "x64" in path.parts else (
                "x86" if "x86" in path.parts else "?")
            index[(arch, path.name)] = path
    return index


def old_campaign(name: str, records: list, index: dict) -> dict:
    duplicates = Counter(record.get("file") for record in records)
    duplicate_records = sum(count - 1 for count in duplicates.values()
                            if count > 1)
    missing_hash = unreadable = bad_numbers = bad_date = 0
    hashes = set()
    zero = detected = 0
    totals = Counter()
    missing_artifacts = []
    date_min = date_max = None
    for record in records:
        file_path = record.get("file", "")
        malicious = record.get("malicious")
        total = record.get("total_scans")
        if not isinstance(malicious, int) or not isinstance(total, int) \
                or not (0 <= malicious <= total) or total < 50:
            bad_numbers += 1
            totals["invalid"] += 1
            continue
        date = parse_date(record.get("date"))
        if date is None:
            bad_date += 1
        else:
            date_min = date if date_min is None or date < date_min else date_min
            date_max = date if date_max is None or date > date_max else date_max
        arch = "x64" if "\\x64\\" in file_path or "/x64/" in file_path else (
            "x86" if "\\x86\\" in file_path or "/x86/" in file_path else "?")
        path = index.get((arch, Path(file_path.replace("\\", "/")).name))
        if path is None:
            missing_artifacts.append(file_path)
            totals["missing_artifact"] += 1
            continue
        try:
            hashes.add(sha256(path))
        except OSError:
            unreadable += 1
            totals["unreadable"] += 1
            continue
        if malicious == 0:
            zero += 1
            totals["zero_detections"] += 1
        else:
            detected += 1
            totals["detected"] += 1
    return {
        "name": name,
        "records": len(records),
        "unique_file_paths": len(duplicates),
        "duplicate_records": duplicate_records,
        "unique_artifacts": len(hashes),
        "verifiable_records": len(records) - len(missing_artifacts)
        - unreadable - bad_numbers,
        "unverifiable_records": len(missing_artifacts),
        "missing_artifacts": len(missing_artifacts),
        "missing_artifact_sample": missing_artifacts[:5],
        "unreadable_artifacts": unreadable,
        "invalid_records": bad_numbers,
        "invalid_dates": bad_date,
        "date_min": date_min.isoformat() if date_min else None,
        "date_max": date_max.isoformat() if date_max else None,
        "zero_detections": zero,
        "detected": detected,
        "status_counts": dict(totals),
    }


def new_campaign(manifest_path: Path, results_path: Path) -> dict:
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    unique = {}
    for entry in entries:
        unique.setdefault(entry["sha256"], entry)
    latest = {}
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            latest[record["sha256"]] = record

    hash_mismatch = missing_file = completed = pending = missing = 0
    bad_stats = 0
    zero = detected = 0
    engine_sums = Counter()
    dates = []
    totals_seen = []
    unsupported = []
    duplicate_manifest = len(entries) - len(unique)
    for digest, entry in unique.items():
        path = ROOT / entry["path"]
        if not path.exists():
            missing_file += 1
            continue
        if sha256(path) != digest:
            hash_mismatch += 1
            continue
        record = latest.get(digest)
        if record is None:
            missing += 1
            continue
        if record.get("status") != "completed":
            pending += 1
            continue
        stats = record.get("stats") or {}
        total = sum(stats.values()) if stats else 0
        if not stats or total != record.get("total") or total < 50:
            bad_stats += 1
            continue
        completed += 1
        engine_sums.update(stats)
        totals_seen.append(total)
        unsupported.append(stats.get("type-unsupported", 0))
        date = parse_date(record.get("date"))
        if date:
            dates.append(date)
        if record.get("malicious", 0) == 0:
            zero += 1
        else:
            detected += 1
    return {
        "manifest_entries": len(entries),
        "unique_hashes": len(unique),
        "duplicate_manifest_entries": duplicate_manifest,
        "missing_files": missing_file,
        "hash_mismatch": hash_mismatch,
        "completed": completed,
        "pending_or_incomplete": pending,
        "missing_result": missing,
        "invalid_stats": bad_stats,
        "zero_detections": zero,
        "detected": detected,
        "engine_totals": dict(engine_sums),
        "total_min": min(totals_seen) if totals_seen else None,
        "total_max": max(totals_seen) if totals_seen else None,
        "type_unsupported_mean": (sum(unsupported) / len(unsupported)
                                  if unsupported else None),
        "date_min": min(dates).isoformat() if dates else None,
        "date_max": max(dates).isoformat() if dates else None,
    }


def main() -> int:
    index = build_index([
        ROOT / "mutations" / "mutations" / "x64",
        ROOT / "mutations" / "mutations" / "x86",
        ROOT / "sgn_mutated" / "x64",
        ROOT / "sgn_mutated" / "x86",
        ROOT / "original_pl" / "x64",
        ROOT / "original_pl" / "x86",
    ])
    audit = {
        "old_native": old_campaign(
            "results.json",
            json.loads((ROOT / "results.json").read_text(encoding="utf-8")),
            index),
        "old_originals": old_campaign(
            "results_original.json",
            json.loads((ROOT / "results_original.json").read_text(
                encoding="utf-8")), index),
        "old_sgn": old_campaign(
            "results_sgn.json",
            json.loads((ROOT / "results_sgn.json").read_text(
                encoding="utf-8")), index),
        "new_mutants": new_campaign(
            ROOT / "vt_manifest.json", ROOT / "tmp" / "vt_results.jsonl"),
        "new_originals": new_campaign(
            ROOT / "vt_originals.json",
            ROOT / "tmp" / "vt_results_original.jsonl"),
    }
    output = ROOT / "bench" / "results" / "vt_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    lines = ["# Audit dei report VirusTotal esistenti", "",
             "Nessuna nuova sottomissione: solo verifica degli artefatti già "
             "presenti. Un record è **verificabile** solo se il file è ancora "
             "su disco e il suo SHA-256 è stato ricalcolato.", ""]
    lines += ["| Dataset | Record | Verificabili | Non verificabili | Hash unici | "
              "Zero rilevamenti | Rilevati |", "|---|---:|---:|---:|---:|---:|---:|"]
    for key, label in (("old_native", "results.json (2025)"),
                       ("old_originals", "results_original.json (2025)"),
                       ("old_sgn", "results_sgn.json (2025)")):
        item = audit[key]
        lines.append(f"| {label} | {item['records']} | "
                     f"{item['verifiable_records']} | "
                     f"{item['unverifiable_records']} | "
                     f"{item['unique_artifacts']} | "
                     f"{item['zero_detections']} | {item['detected']} |")
    for key, label in (("new_mutants", "manifest 2026"),
                       ("new_originals", "originali 2026")):
        item = audit[key]
        lines.append(f"| {label} | {item['unique_hashes']} | "
                     f"{item['completed']} | "
                     f"{item['pending_or_incomplete'] + item['missing_result']} | "
                     f"{item['unique_hashes']} | {item['zero_detections']} | "
                     f"{item['detected']} |")
    lines += ["", "## Controlli di integrità", ""]
    new = audit["new_mutants"]
    engine_total = sum(new["engine_totals"].values())
    unsupported = new["engine_totals"].get("type-unsupported", 0)
    timeouts = new["engine_totals"].get("timeout", 0) + \
        new["engine_totals"].get("confirmed-timeout", 0)
    failures = new["engine_totals"].get("failure", 0)
    lines += [
        f"- Manifest 2026: {new['manifest_entries']} righe, "
        f"{new['unique_hashes']} SHA-256 unici, "
        f"{new['duplicate_manifest_entries']} duplicati nel manifest.",
        f"- Hash dei file 2026 ricontrollati: {new['hash_mismatch']} mismatch, "
        f"{new['missing_files']} file mancanti, "
        f"{new['invalid_stats']} record con stats incoerenti.",
        f"- Scansioni 2026: {new['completed']} completate, "
        f"{new['pending_or_incomplete']} incomplete, "
        f"{new['missing_result']} senza risultato.",
        f"- Date 2026: {new['date_min']} .. {new['date_max']}.",
        f"- Esiti motori 2026 su {engine_total} risposte: "
        f"{unsupported} `type-unsupported` ({100 * unsupported / engine_total:.1f}%), "
        f"{timeouts} timeout, {failures} failure. Il numero di motori che "
        f"hanno davvero analizzato il formato è quindi inferiore al totale "
        f"({new['total_min']}..{new['total_max']}).",
        f"- Ogni file 2026 ha in media "
        f"{new['type_unsupported_mean']:.1f} motori che non supportano il "
        "formato: i confronti '0/N' vanno letti su N meno questi.",
    ]
    old = audit["old_native"]
    olds = audit["old_originals"]
    lines += [
        f"- 2025 `results.json`: {old['verifiable_records']} record "
        f"verificabili e {old['unverifiable_records']} non verificabili "
        "(artefatto assente dal disco: il risultato non è ricontrollabile). "
        f"{old['duplicate_records']} record duplicati, "
        f"{old['invalid_records']} record numerici invalidi, "
        f"{old['invalid_dates']} date invalide.",
        f"- 2025 originali: {olds['records']} record ma solo "
        f"{olds['unique_artifacts']} hash distinti: i campioni non sono "
        "indipendenti.",
        f"- 2025 date: {old['date_min']} .. {old['date_max']}.",
        "",
        "## Zero rilevamenti non significa invisibilità",
        "",
        "Un record con `malicious = 0` è una scansione completata in cui "
        "nessun motore ha classificato il file come malicious in quel "
        "momento; non dimostra che il file sia invisibile, né copre "
        "esecuzione dinamica, sandbox o motori che non supportano il formato "
        "(`type-unsupported`). I conteggi sopra separano zero rilevamenti, "
        "analisi incompleta e risultato mancante. Inoltre output identici "
        "condividono lo stesso hash e non sono campioni indipendenti.",
        "",
    ]
    (ROOT / "bench" / "VT_AUDIT.md").write_text("\n".join(lines),
                                                encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
