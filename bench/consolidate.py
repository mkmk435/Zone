#!/usr/bin/env python3
"""Consolidate every available test result into three CSV files.

Sources (read-only):
  new benchmark : bench/results/*.jsonl, bench/fixtures/*.json
  previous 2026 : tmp/wrap_report.csv + mutations_wrap/manifest.jsonl,
                  tmp/llm_morph_report.csv + tmp/llm_run/stats,
                  tmp/llm_data_report.csv + tmp/lldata_run/stats
  legacy 2025   : test_report.txt, results.json, results_original.json,
                  results_sgn.json
  VT audit      : bench/results/vt_audit.json

Outputs:
  bench/results/all_test_runs.csv
  bench/results/coverage_matrix.csv
  bench/results/remaining_gaps.csv
  bench/results/consolidated_summary.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
sys.path.insert(0, str(ROOT / "tmp"))
import work_rate_data as W  # noqa: E402

RUN_FIELDS = [
    "campaign", "corpus", "test_type", "case", "arch", "technique", "shot",
    "engine_version", "seed", "config", "granularity", "attempt_id",
    "attempts", "build_ok", "exec_ok", "correct", "unique_output_sha256",
    "cost_usd", "source_file", "notes", "class_exact", "class_missed_bytes",
    "class_false_positive_bytes", "vt_scans", "vt_completed",
    "vt_zero_detections", "vt_detected", "vt_unverifiable",
]
MATRIX_FIELDS = [
    "campaign", "corpus", "test_type", "case", "arch", "technique", "shot",
    "engine_version", "attempts", "build_ok", "exec_ok", "correct",
    "class_exact_runs", "class_runs",
    "unique_outputs", "produced", "build_rate", "correct_over_build",
    "correct_over_attempts", "unique_over_produced", "source",
]
GAP_FIELDS = ["corpus", "case", "arch", "technique", "shot", "engine_version",
              "missing", "reason", "priority", "source"]

RUNS = []


def add(**kwargs):
    row = {field: "" for field in RUN_FIELDS}
    row.update(kwargs)
    RUNS.append(row)


def jsonl(path: Path) -> list:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report_map(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    for row in csv.reader(path.open(encoding="utf-8", errors="replace")):
        if len(row) >= 3 and "/" in row[0]:
            out[row[0].split("/")[-1]] = row
    return out


def stem(name: str) -> str:
    return name[:-4] if name.endswith(".bin") else name


# ------------------------------------------------------------------ new bench
def new_benchmark():
    case_list = json.loads(
        (HERE / "fixtures" / "cases.json").read_text(encoding="utf-8"))
    cases = {case["name"]: case for case in case_list}
    for row in jsonl(RESULTS / "native_attempts.jsonl"):
        if row["technique"] == "xd":
            add(campaign="bench_block1_baseline", corpus="benign13",
                test_type="functional", case=row["case"], arch=row["arch"],
                technique="xd", engine_version="2026-11-13_block1",
                config="-xd", granularity="run", attempt_id="baseline",
                attempts=1, build_ok=int(row["build_ok"]),
                exec_ok=int(row["exec_ok"]), correct=int(row["match"]),
                unique_output_sha256=row["sha256"] or "",
                source_file="bench/results/native_attempts.jsonl",
                notes="estrazione simbolica -xd")
            continue
        add(campaign="bench_block1_native", corpus="benign13",
            test_type="functional", case=row["case"], arch=row["arch"],
            technique=row["technique"], engine_version="2026-11-13_block1",
            seed=str(row.get("seed") or ""),
            config=" ".join(str(flag) for flag in row.get("flags", [])),
            granularity="run", attempt_id=f"run{row['run']}",
            attempts=1, build_ok=int(row["build_ok"]),
            exec_ok=int(row["exec_ok"]), correct=int(row["match"]),
            unique_output_sha256=row["sha256"] or "",
            source_file="bench/results/native_attempts.jsonl",
            notes="; ".join(str(flag) for flag in row.get("flags", [])))
    for row in jsonl(RESULTS / "native_wrap86.jsonl"):
        if row["technique"] == "xd":
            add(campaign="bench_block2_baseline", corpus="benign13",
                test_type="functional", case=row["case"], arch=row["arch"],
                technique="xd", engine_version="2026-11-13_block2",
                config="-xd", granularity="run", attempt_id="baseline",
                attempts=1, build_ok=int(row["build_ok"]),
                exec_ok=int(row["exec_ok"]), correct=int(row["match"]),
                unique_output_sha256=row["sha256"] or "",
                source_file="bench/results/native_wrap86.jsonl",
                notes="estrazione simbolica -xd")
            continue
        add(campaign="bench_block2_wrap86", corpus="benign13",
            test_type="functional", case=row["case"], arch=row["arch"],
            technique=row["technique"], engine_version="2026-11-13_block2",
            seed=str(row.get("seed") or ""),
            config=" ".join(str(flag) for flag in row.get("flags", [])),
            granularity="run", attempt_id=f"run{row['run']}",
            attempts=1, build_ok=int(row["build_ok"]),
            exec_ok=int(row["exec_ok"]), correct=int(row["match"]),
            unique_output_sha256=row["sha256"] or "",
            source_file="bench/results/native_wrap86.jsonl",
            notes="; ".join(str(flag) for flag in row.get("flags", [])))
    for row in jsonl(RESULTS / "llm_attempts.jsonl"):
        add(campaign="bench_block1_llm", corpus="benign13",
            test_type="functional", case=row["case"], arch=row["arch"],
            technique=row["technique"], shot=row["shots"],
            engine_version="2026-11-13_block1", granularity="call",
            config=f"--llm -{row['technique']} --llm-shots {row['shots']} "
                   "--llm-retries 1",
            attempt_id=f"call{row['call']}", attempts=1,
            build_ok=int(row["build_ok"]), exec_ok=int(row["exec_ok"]),
            correct=int(row["match"]),
            unique_output_sha256=row["sha256"] or "",
            cost_usd=round(row.get("cost_usd") or 0.0, 6),
            source_file="bench/results/llm_attempts.jsonl",
            notes=row.get("error") or "")
    for row in jsonl(RESULTS / "llm_attempts_x86.jsonl"):
        add(campaign="bench_block2_llm", corpus="benign13",
            test_type="functional", case=row["case"], arch=row["arch"],
            technique=row["technique"], shot=row["shots"],
            engine_version="2026-11-13_block2", granularity="call",
            config=f"--llm -{row['technique']} --llm-shots {row['shots']} "
                   "--llm-retries 1",
            attempt_id=f"call{row['call']}", attempts=1,
            build_ok=int(row["build_ok"]), exec_ok=int(row["exec_ok"]),
            correct=int(row["match"]),
            unique_output_sha256=row["sha256"] or "",
            cost_usd=round(row.get("cost_usd") or 0.0, 6),
            source_file="bench/results/llm_attempts_x86.jsonl",
            notes=row.get("error") or "")
    for row in jsonl(RESULTS / "llm_data_attempts.jsonl"):
        add(campaign="bench_block2_classifier", corpus="benign13",
            test_type="classifier", case=row["case"], arch=row["arch"],
            technique="llm-data", engine_version="2026-11-13_block2",
            config="--llm-data --llm-retries 1",
            granularity="call", attempt_id=f"call{row['call']}",
            attempts=1, build_ok=int(row["build_ok"]),
            exec_ok=int(row["exec_ok"]), correct=int(row["match"]),
            unique_output_sha256=row["sha256"] or "",
            cost_usd=round(row.get("cost_usd") or 0.0, 6),
            class_exact=int(bool((row.get("classification") or {})
                                 .get("exact_match"))),
            source_file="bench/results/llm_data_attempts.jsonl",
            notes=(row.get("classification") or {}).get("exact_match") and
            "classificazione esatta" or row.get("error", ""))
    for row in jsonl(RESULTS / "classifier_compare.jsonl"):
        evaluation = row["evaluation"]
        add(campaign="bench_block2_classifier_fixtures",
            corpus="classifier6", test_type="classifier", case=row["case"],
            arch=row["arch"], technique=row["method"],
            engine_version="2026-11-13_block2", granularity="call",
            config=("--llm-data --llm-retries 1"
                    if row["method"] == "llm" else "-xd"),
            attempt_id=f"call{row['call']}", attempts=1,
            build_ok=int(row["build_ok"]), exec_ok=int(row["exec_ok"]),
            correct=int(row["match"]),
            unique_output_sha256=row["sha256"] or "",
            cost_usd=round(row.get("cost_usd") or 0.0, 6),
            source_file="bench/results/classifier_compare.jsonl",
            class_exact=int(evaluation["exact"]),
            class_missed_bytes=evaluation["missed_bytes"],
            class_false_positive_bytes=evaluation["code_false_positive_bytes"],
            notes=f"predicted={evaluation['predicted']} "
                  f"truth={evaluation['truth']}")
    # baselines: original fixtures
    for case in case_list:
        add(campaign="baseline_original_fixtures", corpus="benign13",
            test_type="functional", case=case["name"], arch=case["arch"],
            technique="original", engine_version="none", granularity="run",
            config="(payload originale)", attempt_id="original", attempts=1,
            build_ok=int(case["original_ok"]), exec_ok=int(case["original_ok"]),
            correct=int(case["original_ok"]),
            unique_output_sha256=case["sha256"],
            source_file="bench/fixtures/cases.json",
            notes="payload originale, risultato atteso verificato")
    # pilots (not part of the matrix)
    for row in jsonl(RESULTS / "native_smoke.jsonl"):
        add(campaign="pilot_native_smoke", corpus="benign13",
            test_type="functional", case=row["case"], arch=row["arch"],
            technique=row["technique"], engine_version="2026-11-13_block1",
            granularity="run", attempt_id="smoke", attempts=1,
            build_ok=int(row["build_ok"]), exec_ok=int(row["exec_ok"]),
            correct=int(row["match"]), unique_output_sha256=row["sha256"] or "",
            source_file="bench/results/native_smoke.jsonl",
            notes="prova pilota, esclusa dalla matrice")
    pilot_stats = ROOT / "bench" / "run" / "llm86_pilot" / "stats.json"
    if pilot_stats.exists():
        stats = json.loads(pilot_stats.read_text(encoding="utf-8"))
        add(campaign="pilot_llm_x86", corpus="non_corpus_smoke",
            test_type="functional", case="x86_smoke", arch="x86",
            technique="eq", shot=0, engine_version="2026-11-13_block2",
            granularity="cell", attempt_id="pilot", attempts=stats.get("attempts", 1),
            build_ok=1, exec_ok="", correct="",
            cost_usd=round((stats.get("cost_usd") or {}).get("total") or 0.0, 6),
            source_file="bench/run/llm86_pilot/stats.json",
            notes="verifica di supporto LLM x86, fuori corpus")


# ------------------------------------------------------------- previous 2026
def previous_2026():
    report = report_map(ROOT / "tmp" / "wrap_report.csv")
    manifest_map = {}
    for record in jsonl(ROOT / "mutations_wrap" / "manifest.jsonl"):
        key = (record["payload"], record["tech"], record["index"])
        previous = manifest_map.get(key)
        successful = record["status"] in ("ok", "exists")
        if previous is None or (successful and previous["status"]
                                not in ("ok", "exists")):
            manifest_map[key] = record
    for record in manifest_map.values():
        name = Path(record["out"]).name
        build = record["status"] in ("ok", "exists")
        row = report.get(name)
        correct = bool(build and row and row[2].upper() == "OK")
        output = ROOT / record["out"]
        add(campaign="prev_2026_wrap", corpus="metasploit_low13_x64",
            test_type="functional", case=record["payload"], arch="x64",
            technique=record["tech"], engine_version="tmp/wrap_snapshot",
            seed=str(record.get("seed") or ""),
            config=" ".join(["-xd", f"-{record['tech']}"]),
            granularity="run", attempt_id=f"run{record['index']}",
            attempts=1, build_ok=int(build), exec_ok=int(correct),
            correct=int(correct),
            unique_output_sha256=sha256(output) if output.exists() else "",
            source_file="mutations_wrap/manifest.jsonl + tmp/wrap_report.csv",
            notes=(row[3] if row and len(row) > 3 else "")
            or (record.get("error") or "")[-200:])
    llm_report = report_map(ROOT / "tmp" / "llm_morph_report.csv")
    stats_dir = ROOT / "tmp" / "llm_run" / "stats"
    for stats_path in sorted(stats_dir.glob("*.json")):
        match = re.match(r"windows_x64_messagebox_llm_([a-z]+)_s([02])_(\d+)\.json$",
                         stats_path.name)
        if not match:
            continue
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        output = ROOT / "mutations_llm" / "x64" / (
            stats_path.stem + ".bin")
        report = llm_report.get(output.name)
        report_ok = bool(report and report[2].upper() == "OK")
        calls = stats.get("api_call_details") or []
        details = stats.get("attempt_details") or []
        for index, detail in enumerate(details):
            cost = 0.0
            if index < len(calls):
                cost = calls[index].get("cost_usd") or 0.0
            accepted = bool(detail.get("accepted"))
            add(campaign="prev_2026_llm", corpus="metasploit_messagebox_x64",
                test_type="functional", case="windows_x64_messagebox",
                arch="x64", technique=match.group(1), shot=int(match.group(2)),
                engine_version="tmp/wrap_snapshot", granularity="call",
                config=f"--llm -{match.group(1)} "
                       f"--llm-shots {match.group(2)}",
                attempt_id=f"mutation{match.group(3)}_attempt{index + 1}",
                attempts=1, build_ok=int(accepted),
                exec_ok=int(accepted and report_ok),
                correct=int(accepted and report_ok),
                unique_output_sha256=(sha256(output)
                                      if accepted and output.exists() else ""),
                cost_usd=round(cost, 6),
                source_file="tmp/llm_run/stats/*.json + tmp/llm_morph_report.csv",
                notes=(detail.get("error") or "")[-200:])
    data_report = report_map(ROOT / "tmp" / "llm_data_report.csv")
    data_dir = ROOT / "tmp" / "lldata_run" / "stats"
    for stats_path in sorted(data_dir.glob("*.json")):
        if stats_path.name.endswith(".data.json"):
            continue
        stem_name = stats_path.stem
        output = None
        for directory in ("x64", "x86"):
            candidate = ROOT / "mutations_llm_data" / directory / \
                (stem_name + ".bin")
            if candidate.exists():
                output = candidate
                break
        report = data_report.get((stem_name + ".bin")) if output else None
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        attempts = stats.get("attempts", 0) or 0
        cost = (stats.get("cost_usd") or {}).get("total") or 0.0
        extra = stats_path.with_name(stats_path.name + ".data.json")
        if extra.exists():
            extra_stats = json.loads(extra.read_text(encoding="utf-8"))
            attempts += extra_stats.get("attempts", 0) or 0
            cost += (extra_stats.get("cost_usd") or {}).get("total") or 0.0
        arch = "x86" if output and "/x86/" in str(output).replace("\\", "/") \
            else "x64"
        base_name, run_index = stem_name.rsplit("_", 1)
        add(campaign="prev_2026_classifier", corpus="metasploit5",
            test_type="classifier", case=base_name,
            arch=arch, technique="llm-data",
            engine_version="tmp/wrap_snapshot", granularity="cell",
            config="--llm-data",
            attempt_id=f"run{run_index}", attempts=attempts,
            build_ok=int(bool(report and report[2].upper() == "OK")),
            exec_ok=int(bool(report and report[2].upper() == "OK")),
            correct=int(bool(report and report[2].upper() == "OK")),
            unique_output_sha256=sha256(output) if output else "",
            cost_usd=round(cost, 6),
            source_file="tmp/lldata_run/stats/*.json + tmp/llm_data_report.csv",
            notes="")


# ----------------------------------------------------------------- legacy 2025
def legacy():
    aggregate = defaultdict(lambda: [0, 0])
    path = ROOT / "test_report.txt"
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            row = line.split(",", 3)
            if len(row) < 3 or "/" not in row[0]:
                continue
            arch, base, tech = W.parse_path(row[0])
            aggregate[(arch, base, tech)][0] += 1
            aggregate[(arch, base, tech)][1] += row[2].strip().upper() == "OK"
    for (arch, base, tech), (attempts, ok) in sorted(aggregate.items()):
        add(campaign="legacy_2025_working", corpus="metasploit102",
            test_type="functional", case=base, arch=arch, technique=tech,
            engine_version="legacy_2025_unfrozen", config=f"-{tech}",
            granularity="cell", attempt_id="summary", attempts=attempts, build_ok="",
            exec_ok="", correct=ok,
            source_file="test_report.txt",
            notes="riepilogo da righe grezze; build non registrata; "
                  "artefatto non riverificato")


def vt_rows():
    audit = json.loads((RESULTS / "vt_audit.json").read_text(encoding="utf-8"))
    labels = {
        "old_native": ("legacy_2025_vt", "results.json"),
        "old_originals": ("legacy_2025_vt_originals", "results_original.json"),
        "old_sgn": ("legacy_2025_vt_sgn", "results_sgn.json"),
    }
    for key, (campaign, source) in labels.items():
        item = audit[key]
        add(campaign=campaign, corpus="metasploit102", test_type="vt_historical",
            case="(dataset)", arch="both", technique="all",
            engine_version="legacy_2025", granularity="summary",
            attempt_id="summary", attempts=item["records"], build_ok="",
            exec_ok="", correct=item["detected"],
            source_file=source,
            notes=f"verificabili={item['verifiable_records']}; "
                  f"non_verificabili={item['unverifiable_records']}; "
                  f"zero={item['zero_detections']}",
            vt_scans=item["records"],
            vt_completed=item["verifiable_records"],
            vt_zero_detections=item["zero_detections"],
            vt_detected=item["detected"],
            vt_unverifiable=item["unverifiable_records"])
    for key, campaign, source in (
            ("new_mutants", "prev_2026_vt", "vt_manifest.json"),
            ("new_originals", "prev_2026_vt_originals", "vt_originals.json")):
        item = audit[key]
        add(campaign=campaign, corpus="metasploit_2026", test_type="vt_historical",
            case="(dataset)", arch="both", technique="all",
            engine_version="2026-11-13", granularity="summary",
            attempt_id="summary", attempts=item["unique_hashes"], build_ok="",
            exec_ok="", correct=item["detected"], source_file=source,
            notes=f"completate={item['completed']}; "
                  f"incomplete={item['pending_or_incomplete']}; "
                  f"senza_risultato={item['missing_result']}",
            vt_scans=item["unique_hashes"], vt_completed=item["completed"],
            vt_zero_detections=item["zero_detections"],
            vt_detected=item["detected"],
            vt_unverifiable=item["pending_or_incomplete"] + item["missing_result"])


# --------------------------------------------------------------- aggregation
def write_csv(path: Path, fields: list, rows: list):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def matrix_rows():
    groups = defaultdict(list)
    for row in RUNS:
        if row["test_type"] == "vt_historical":
            continue
        key = (row["campaign"], row["corpus"], row["test_type"],
               row["case"], row["arch"], row["technique"], row["shot"],
               row["engine_version"])
        groups[key].append(row)
    out = []
    for key in sorted(groups):
        rows = groups[key]
        attempts = sum(int(row["attempts"] or 0) for row in rows)
        build = sum(int(row["build_ok"]) for row in rows
                    if row["build_ok"] != "")
        exec_ok = sum(int(row["exec_ok"]) for row in rows
                      if row["exec_ok"] != "")
        correct = sum(int(row["correct"]) for row in rows
                      if row["correct"] != "")
        hashes = {row["unique_output_sha256"] for row in rows
                  if row["unique_output_sha256"]}
        has_build = any(row["build_ok"] != "" for row in rows)
        class_rows = [row for row in rows if row["class_exact"] != ""]
        out.append({
            "campaign": key[0], "corpus": key[1], "test_type": key[2],
            "case": key[3], "arch": key[4], "technique": key[5],
            "shot": key[6], "engine_version": key[7],
            "attempts": attempts, "build_ok": build if has_build else "",
            "exec_ok": exec_ok if has_build else "",
            "correct": correct,
            "class_exact_runs": sum(int(row["class_exact"])
                                    for row in class_rows) if class_rows else "",
            "class_runs": len(class_rows) if class_rows else "",
            "unique_outputs": len(hashes) if hashes else "",
            "produced": build if has_build else "",
            "build_rate": round(build / attempts, 4) if has_build and attempts else "",
            "correct_over_build": round(correct / build, 4) if has_build and build else "",
            "correct_over_attempts": round(correct / attempts, 4) if attempts else "",
            "unique_over_produced": round(len(hashes) / build, 4)
            if has_build and build and hashes else "",
            "source": "; ".join(sorted({row["source_file"] for row in rows
                                        if row["source_file"]})),
        })
    return out


def gap_rows(matrix):
    gaps = []
    expected = defaultdict(int)
    for arch in ("x64", "x86"):
        cases = [case for case in json.loads(
            (HERE / "fixtures" / "cases.json").read_text(encoding="utf-8"))
            if case["arch"] == arch]
        techniques = ["eq", "nop", "bcf", "ibp", "wrap"]
        for case in cases:
            for technique in techniques:
                expected[("benign13", case["name"], arch, technique, "",
                          "2026-11-13_block1")] = 3
            for technique in ("eq", "nop", "bcf", "ibp"):
                for shot in (0, 2):
                    expected[("benign13", case["name"], arch, technique,
                              shot, "2026-11-13_block1")] = 3
    observed = Counter()
    matrix_campaigns = {"bench_block1_native", "bench_block2_wrap86",
                        "bench_block1_llm", "bench_block2_llm"}
    for row in matrix:
        if row["corpus"] != "benign13" or row["test_type"] != "functional":
            continue
        if row["campaign"] not in matrix_campaigns:
            continue
        key = (row["corpus"], row["case"], row["arch"], row["technique"],
               int(row["shot"]) if row["shot"] != "" else "",
               row["engine_version"])
        observed[key] += int(row["attempts"])
    for key, wanted in sorted(expected.items(), key=lambda item: str(item[0])):
        have = 0
        for (corpus, case, arch, technique, shot, version), count in observed.items():
            if (corpus, case, arch, technique, shot) == key[:5]:
                have += count
        if have < wanted:
            gaps.append({
                "corpus": key[0], "case": key[1], "arch": key[2],
                "technique": key[3], "shot": key[4],
                "engine_version": key[5], "missing": wanted - have,
                "reason": "cella non eseguita o incompleta",
                "priority": "alta" if key[3] in ("eq", "nop", "bcf", "ibp")
                else "media",
                "source": "confronto matrice attesa/oss",
            })
    gaps.append({
        "corpus": "benign13", "case": "(tutte)", "arch": "both",
        "technique": "pii/ip", "shot": "", "engine_version": "",
        "missing": 2 * 13 * 3, "reason": "tecniche layout-owning fuori "
        "matrice per scelta documentata", "priority": "bassa",
        "source": "bench/BENCH_REPORT.md",
    })
    gaps.append({
        "corpus": "classifier6", "case": "(tutte)", "arch": "both",
        "technique": "vt", "shot": "", "engine_version": "2026-11-13",
        "missing": 0, "reason": "nessuna sottomissione VT per il corpus "
        "benigno (richiesta esplicita: solo report storici in lettura)",
        "priority": "n/a", "source": "istruzioni utente",
    })
    gaps.append({
        "corpus": "metasploit102", "case": "(tutte)", "arch": "both",
        "technique": "vt", "shot": "", "engine_version": "legacy_2025",
        "missing": audit_unverifiable(), "reason": "artefatti 2025 assenti: "
        "record VT non verificabili", "priority": "alta",
        "source": "bench/VT_AUDIT.md",
    })
    gaps.append({
        "corpus": "metasploit102", "case": "(tutte)", "arch": "both",
        "technique": "build", "shot": "", "engine_version": "legacy_2025",
        "missing": 15020, "reason": "i report 2025 non registrano build/esito "
        "per tentativo: solo working rate", "priority": "media",
        "source": "test_report.txt",
    })
    return gaps


def audit_unverifiable() -> int:
    audit = json.loads((RESULTS / "vt_audit.json").read_text(encoding="utf-8"))
    return audit["old_native"]["unverifiable_records"]


def main() -> int:
    new_benchmark()
    previous_2026()
    legacy()
    vt_rows()
    write_csv(RESULTS / "all_test_runs.csv", RUN_FIELDS, RUNS)
    matrix = matrix_rows()
    write_csv(RESULTS / "coverage_matrix.csv", MATRIX_FIELDS, matrix)
    gaps = gap_rows(matrix)
    write_csv(RESULTS / "remaining_gaps.csv", GAP_FIELDS, gaps)
    summary = {
        "runs": len(RUNS),
        "campaigns": dict(Counter(row["campaign"] for row in RUNS)),
        "matrix_rows": len(matrix),
        "gaps": len(gaps),
        "missing_cells": sum(int(gap["missing"]) for gap in gaps
                             if gap["reason"].startswith("cella")),
    }
    (RESULTS / "consolidated_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
