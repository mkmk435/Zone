"""Shared parsing/aggregation for the working-rate regression."""
import csv
import os
import re
import collections

TECH_TOKENS = {"nop", "eq", "pii", "bcf", "ibp"}
TECHS = [
    "nop", "eq", "pii", "bcf", "ibp",
    "eq_nop_pii", "eq_nop_bcf", "eq_nop_ibp",
    "nop_eq", "nop_pii", "nop_bcf", "nop_ibp",
    "eq_pii", "eq_bcf", "eq_ibp",
]
TECH_FLAGS = {
    "nop": ["-nop"],
    "eq": ["-eq"],
    "pii": ["-pii"],
    "bcf": ["-bcf"],
    "ibp": ["-ibp"],
    "eq_nop_pii": ["-eq", "-nop", "-pii"],
    "eq_nop_bcf": ["-eq", "-nop", "-bcf"],
    "eq_nop_ibp": ["-eq", "-nop", "-ibp"],
    "nop_eq": ["-nop", "-eq"],
    "nop_pii": ["-nop", "-pii"],
    "nop_bcf": ["-nop", "-bcf"],
    "nop_ibp": ["-nop", "-ibp"],
    "eq_pii": ["-eq", "-pii"],
    "eq_bcf": ["-eq", "-bcf"],
    "eq_ibp": ["-eq", "-ibp"],
}
# Extraction-only configurations requested explicitly by the user.
EXTRA_TECHS = ["xd", "xd_ebi"]
ALL_TECHS = TECHS + EXTRA_TECHS


def flags_for(tech):
    if tech == "xd":
        return ["-xd"]
    if tech == "xd_ebi":
        return ["-xd", "-ebi"]
    return ["-xd", "-ebi"] + TECH_FLAGS[tech]


def parse_path(path):
    p = path.replace("\\", "/")
    arch = "x64" if "x64" in p else "x86"
    name = os.path.basename(p)
    stem = re.sub(r"\.bin$", "", name)
    stem = re.sub(r"_\d+$", "", stem)
    if stem.endswith("_xd_ebi"):
        return arch, stem[:-len("_xd_ebi")], "xd_ebi"
    if stem.endswith("_xd"):
        return arch, stem[:-len("_xd")], "xd"
    parts = stem.split("_")
    tech = []
    while parts and parts[-1] in TECH_TOKENS:
        tech.append(parts.pop())
    return arch, "_".join(parts), "_".join(reversed(tech))


def load_report(path):
    """Return dict (arch, base, tech) -> [ok, total] and raw rows."""
    stats = collections.defaultdict(lambda: [0, 0])
    rows = []
    if not os.path.exists(path):
        return stats, rows
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            path_s, kind, result = row[0].strip(), row[1].strip(), row[2].strip().upper()
            arch, base, tech = parse_path(path_s)
            if not tech:
                continue
            s = stats[(arch, base, tech)]
            s[1] += 1
            if result == "OK":
                s[0] += 1
            rows.append((arch, base, tech, kind, result))
    return stats, rows


def load_all_reports(paths):
    merged = collections.defaultdict(lambda: [0, 0])
    rows = []
    for p in paths:
        s, r = load_report(p)
        for k, v in s.items():
            merged[k][0] += v[0]
            merged[k][1] += v[1]
        rows.extend(r)
    return merged, rows


def per_payload(stats):
    d = collections.defaultdict(lambda: [0, 0])
    for (arch, base, tech), (ok, total) in stats.items():
        d[(arch, base)][0] += ok
        d[(arch, base)][1] += total
    return d


def rate(ok, total):
    return (ok / total * 100.0) if total else 0.0


def load_original_names():
    orig = set()
    for arch in ("x64", "x86"):
        d = os.path.join("original_pl", arch)
        for fn in os.listdir(d):
            if fn.endswith(".bin"):
                orig.add((arch, fn[:-4]))
    return orig
