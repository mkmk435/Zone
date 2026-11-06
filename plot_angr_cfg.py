"""Plot an angr CFG beside a byte map for a raw x86/x64 payload.

Install: pip install angr
Example: python plot_angr_cfg.py payload.bin --arch x64

The byte map is evidence for review, not a definitive code/data classifier.
In particular, "uncovered" means angr did not put the bytes in a CFG block.
"""

from __future__ import annotations

import argparse
import html
import json
import math
from collections import Counter
from pathlib import Path


KINDS = ("uncovered", "code", "angr_data", "overlap")
COLORS = {
    "uncovered": "#cbd5e1",
    "code": "#2563eb",
    "angr_data": "#f59e0b",
    "overlap": "#dc2626",
}
BYTES_PER_ROW = 128


def integer(value: str) -> int:
    return int(value, 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path, help="Raw payload bytes")
    parser.add_argument("--arch", required=True, choices=("x86", "x64"))
    parser.add_argument(
        "--entry-offset", type=integer, default=0,
        help="Entry offset within the file (default: 0; accepts 0x...)",
    )
    parser.add_argument(
        "--base-address", type=integer, default=0x400000,
        help="Analysis-only load address (default: 0x400000)",
    )
    parser.add_argument(
        "--output", type=Path,
        help="SVG path (default: <payload stem>_cfg.svg in the current directory)",
    )
    parser.add_argument(
        "--max-nodes", type=int, default=120,
        help="Maximum CFG nodes drawn in SVG; 0 draws all (default: 120)",
    )
    return parser.parse_args()


def collect_cfg(cfg, base: int, length: int):
    end = base + length
    nodes = sorted(
        (
            node for node in cfg.graph.nodes
            if isinstance(getattr(node, "addr", None), int)
            and isinstance(getattr(node, "size", None), int)
            and node.size > 0 and base <= node.addr < end
        ),
        key=lambda node: (node.addr, node.size),
    )
    ids = {node: index for index, node in enumerate(nodes)}
    blocks = [
        {"id": ids[node], "address": node.addr, "offset": node.addr - base,
         "size": node.size}
        for node in nodes
    ]
    edges = [
        {"source": ids[src], "target": ids[dst],
         "jumpkind": str(attributes.get("jumpkind", ""))}
        for src, dst, attributes in cfg.graph.edges(data=True)
        if src in ids and dst in ids
    ]
    inferred_data = [
        {"address": addr, "offset": addr - base, "size": item.size,
         "type": str(getattr(item, "sort", "unknown"))}
        for addr, item in cfg.model.memory_data.items()
        if isinstance(addr, int) and isinstance(getattr(item, "size", None), int)
        and item.size > 0 and addr < end and addr + item.size > base
    ]
    inferred_data.sort(key=lambda item: item["address"])
    return blocks, edges, inferred_data


def classify(raw: bytes, base: int, blocks: list[dict], data: list[dict]):
    # 0: no CFG/data evidence; 1: CFG code; 2: angr data; 3: conflicting evidence.
    states = bytearray(len(raw))
    for block in blocks:
        lo = max(0, block["offset"])
        hi = min(len(raw), block["offset"] + block["size"])
        states[lo:hi] = b"\x01" * (hi - lo)
    for item in data:
        lo = max(0, item["offset"])
        hi = min(len(raw), item["offset"] + item["size"])
        for offset in range(lo, hi):
            states[offset] = 3 if states[offset] in (1, 3) else 2

    ranges = []
    start = 0
    while start < len(raw):
        stop = start + 1
        while stop < len(raw) and states[stop] == states[start]:
            stop += 1
        preview = raw[start:min(stop, start + 24)]
        ranges.append({
            "kind": KINDS[states[start]],
            "offset_start": start,
            "offset_end": stop,  # exclusive
            "address_start": base + start,
            "address_end": base + stop,
            "size": stop - start,
            "hex_preview": preview.hex(" "),
            "ascii_preview": "".join(
                chr(byte) if 32 <= byte < 127 else "." for byte in preview
            ),
        })
        start = stop
    return states, ranges


def write_dot(path: Path, blocks: list[dict], edges: list[dict], entry: int):
    lines = ["digraph cfg {", '  graph [rankdir=TB];',
             '  node [shape=box, fontname="Consolas"];']
    for block in blocks:
        address = block["address"]
        color = "#7c3aed" if address == entry else COLORS["code"]
        lines.append(
            f'  n{block["id"]} [label="0x{address:x}\\n{block["size"]} bytes", '
            f'color="{color}"];'
        )
    for edge in edges:
        lines.append(
            f'  n{edge["source"]} -> n{edge["target"]} '
            f'[label="{edge["jumpkind"]}"];'
        )
    lines.append("}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_svg(
    path: Path, name: str, raw: bytes, base: int, entry: int,
    states: bytearray, ranges: list[dict], blocks: list[dict],
    edges: list[dict], max_nodes: int,
):
    shown = blocks if max_nodes == 0 else blocks[:max_nodes]
    shown_ids = {block["id"] for block in shown}
    grid_columns = 5
    candidates = [item for item in ranges if item["kind"] != "code"]
    actual_map_rows = math.ceil(len(raw) / BYTES_PER_ROW)
    map_rows = max(actual_map_rows, min(13, len(candidates) + 1))
    map_y = 132
    graph_y = map_y + 20 * map_rows + 96
    graph_rows = math.ceil(len(shown) / grid_columns)
    width = 1570
    height = graph_y + max(1, graph_rows) * 100 + 55
    counts = Counter(KINDS[value] for value in states)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" '
        'refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" '
        'fill="none" stroke="#64748b"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        f'<text x="40" y="48" font-size="24" font-family="sans-serif" '
        f'font-weight="bold">angr CFG + byte map: {html.escape(name)}</text>',
        f'<text x="40" y="75" font-size="14" font-family="sans-serif" '
        f'fill="#475569">{len(raw)} bytes · base 0x{base:x} · '
        f'entry offset 0x{entry - base:x} · {len(blocks)} CFG blocks · '
        f'{len(edges)} edges</text>',
    ]
    for index, kind in enumerate(KINDS):
        x = 40 + index * 230
        parts.extend([
            f'<rect x="{x}" y="89" width="15" height="15" '
            f'fill="{COLORS[kind]}"/>',
            f'<text x="{x+22}" y="102" font-size="13" '
            f'font-family="sans-serif">{kind.replace("_", " ")} '
            f'({counts[kind]})</text>',
        ])
    parts.append(
        f'<text x="40" y="{map_y - 9}" font-size="15" '
        f'font-family="sans-serif" font-weight="bold">File offsets '
        f'({BYTES_PER_ROW} bytes per row)</text>'
    )
    for row in range(actual_map_rows):
        row_start = row * BYTES_PER_ROW
        row_end = min(len(raw), row_start + BYTES_PER_ROW)
        y = map_y + row * 20
        parts.append(
            f'<text x="40" y="{y+11}" font-size="12" '
            f'font-family="monospace" fill="#334155">0x{row_start:06x}</text>'
        )
        cursor = row_start
        while cursor < row_end:
            stop = cursor + 1
            while stop < row_end and states[stop] == states[cursor]:
                stop += 1
            kind = KINDS[states[cursor]]
            x = 140 + (cursor - row_start) * 7
            parts.append(
                f'<rect x="{x}" y="{y}" width="{(stop-cursor)*7}" '
                f'height="14" fill="{COLORS[kind]}">'
                f'<title>0x{cursor:x}–0x{stop:x} (exclusive): {kind}</title>'
                f'</rect>'
            )
            cursor = stop

    parts.append(
        f'<text x="1070" y="{map_y-9}" font-size="15" '
        f'font-family="sans-serif" font-weight="bold">Non-CFG ranges</text>'
    )
    for index, item in enumerate(candidates[:12]):
        label = (f'0x{item["offset_start"]:x}–0x{item["offset_end"]:x} '
                 f'{item["kind"]} ({item["size"]} B)')
        parts.append(
            f'<text x="1070" y="{map_y + index*20 + 12}" font-size="12" '
            f'font-family="monospace" fill="#334155">{label}</text>'
        )
    if len(candidates) > 12:
        parts.append(
            f'<text x="1070" y="{map_y + 12*20 + 12}" '
            f'font-size="12" font-family="sans-serif">'
            f'{len(candidates)-12} more ranges in JSON</text>'
        )

    parts.append(
        f'<text x="40" y="{graph_y-28}" font-size="17" '
        f'font-family="sans-serif" font-weight="bold">Control-flow graph</text>'
    )
    if len(shown) < len(blocks):
        parts.append(
            f'<text x="270" y="{graph_y-28}" font-size="13" '
            f'font-family="sans-serif" fill="#b45309">'
            f'Showing {len(shown)} of {len(blocks)} blocks; DOT and JSON contain all.</text>'
        )
    positions = {}
    for index, block in enumerate(shown):
        positions[block["id"]] = (
            55 + (index % grid_columns) * 300,
            graph_y + (index // grid_columns) * 100,
        )
    for edge in edges:
        if edge["source"] not in shown_ids or edge["target"] not in shown_ids:
            continue
        sx, sy = positions[edge["source"]]
        tx, ty = positions[edge["target"]]
        x1, y1 = sx + 112, sy + 56
        x2, y2 = tx + 112, ty - 3
        middle = (y1 + y2) / 2
        parts.append(
            f'<path d="M{x1} {y1} C{x1} {middle}, {x2} {middle}, {x2} {y2}" '
            f'fill="none" stroke="#64748b" stroke-opacity="0.55" '
            f'stroke-width="1.4" marker-end="url(#arrow)"/>'
        )
    for block in shown:
        x, y = positions[block["id"]]
        is_entry = block["address"] == entry
        color = "#7c3aed" if is_entry else COLORS["code"]
        parts.extend([
            f'<rect x="{x}" y="{y}" width="224" height="56" rx="7" '
            f'fill="#ffffff" stroke="{color}" stroke-width="2"/>',
            f'<text x="{x+12}" y="{y+23}" font-size="15" '
            f'font-family="monospace" font-weight="bold">'
            f'0x{block["address"]:x}</text>',
            f'<text x="{x+12}" y="{y+43}" font-size="12" '
            f'font-family="sans-serif" fill="#475569">'
            f'offset 0x{block["offset"]:x} · {block["size"]} bytes'
            f'{" · entry" if is_entry else ""}</text>',
        ])
    parts.append('</svg>')
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main():
    args = parse_args()
    raw = args.payload.read_bytes()
    if not raw:
        raise SystemExit("Payload is empty")
    if not 0 <= args.entry_offset < len(raw):
        raise SystemExit("--entry-offset must be inside the payload")
    if args.max_nodes < 0:
        raise SystemExit("--max-nodes must be at least zero")
    if args.base_address < 0:
        raise SystemExit("--base-address must be nonnegative")

    try:
        import angr
    except ImportError as exc:
        raise SystemExit("angr is required: pip install angr") from exc

    base = args.base_address
    entry = base + args.entry_offset
    project = angr.Project(
        str(args.payload),
        main_opts={"backend": "blob", "arch": "x86" if args.arch == "x86" else "amd64",
                   "base_addr": base, "entry_point": entry},
        auto_load_libs=False,
    )
    cfg = project.analyses.CFGFast(
        start_at_entry=True,
        force_complete_scan=False,
        force_smart_scan=False,
        function_prologues=False,
        symbols=False,
        normalize=True,
        data_references=True,
    )
    blocks, edges, inferred_data = collect_cfg(cfg, base, len(raw))
    states, ranges = classify(raw, base, blocks, inferred_data)

    svg_path = args.output or Path.cwd() / f"{args.payload.stem}_cfg.svg"
    if svg_path.suffix.lower() != ".svg":
        raise SystemExit("--output must end in .svg")
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = svg_path.with_suffix(".json")
    dot_path = svg_path.with_suffix(".dot")
    write_svg(svg_path, args.payload.name, raw, base, entry, states, ranges,
              blocks, edges, args.max_nodes)
    write_dot(dot_path, blocks, edges, entry)
    report = {
        "payload": str(args.payload.resolve()), "architecture": args.arch,
        "base_address": base, "entry_address": entry, "size": len(raw),
        "note": "Uncovered bytes may be data or code missed by static CFG recovery.",
        "byte_counts": dict(Counter(KINDS[value] for value in states)),
        "ranges": ranges, "angr_memory_data": inferred_data,
        "cfg_blocks": blocks, "cfg_edges": edges,
    }
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"CFG: {len(blocks)} blocks, {len(edges)} edges")
    print("Byte counts:", report["byte_counts"])
    print(f"Wrote {svg_path}, {json_path}, {dot_path}")


if __name__ == "__main__":
    main()
