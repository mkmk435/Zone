"""Read-only inventory of candidate text in arbitrary binary files.

This is a strings viewer, not a code/data classifier. Printable instructions
can appear in the results, and non-text data will not appear. Offsets refer to
the file, not to virtual addresses. UTF-16 detection covers printable Latin
characters (U+0020..U+024F), in both byte orders and at both alignments.

Usage:
    python inspect_strings.py FILE
    python inspect_strings.py FILE --hex --limit 0

Library use:
    candidates = extract_strings(binary_bytes, min_length=4)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass(frozen=True)
class StringCandidate:
    start: int
    end: int  # Exclusive; includes the terminator when present.
    encoding: str
    text: str
    terminator_size: int = 0

    @property
    def byte_length(self) -> int:
        return self.end - self.start


def _utf8_character(data: bytes, offset: int) -> tuple[str, int]:
    first = data[offset]
    if first < 0x80:
        return chr(first), 1
    width = (
        2 if 0xC2 <= first <= 0xDF else
        3 if 0xE0 <= first <= 0xEF else
        4 if 0xF0 <= first <= 0xF4 else 1
    )
    try:
        return data[offset:offset + width].decode("utf-8"), width
    except UnicodeDecodeError:
        return "", 1


def _scan_utf8(data: bytes, minimum: int) -> list[StringCandidate]:
    results = []
    position = 0
    while position < len(data):
        start = position
        characters = []
        while position < len(data):
            character, width = _utf8_character(data, position)
            if not character or not character.isprintable():
                break
            characters.append(character)
            position += width
        if len(characters) >= minimum:
            text = "".join(characters)
            if text.strip():
                terminator = int(data[position:position + 1] == b"\x00")
                results.append(StringCandidate(
                    start, position + terminator,
                    "ASCII" if text.isascii() else "UTF-8", text, terminator,
                ))
        # Consume the invalid or non-printable byte; retry subsequent bytes.
        position += 1
    return results


def _scan_utf16_latin(data: bytes, minimum: int) -> list[StringCandidate]:
    results = []
    for byte_order, encoding in (("little", "UTF-16LE"), ("big", "UTF-16BE")):
        for alignment in (0, 1):
            position = alignment
            while position + 1 < len(data):
                start = position
                characters = []
                while position + 1 < len(data):
                    value = int.from_bytes(data[position:position + 2], byte_order)
                    if not (0x20 <= value <= 0x024F and chr(value).isprintable()):
                        break
                    characters.append(chr(value))
                    position += 2
                if len(characters) >= minimum:
                    text = "".join(characters)
                    if text.strip():
                        terminator = 2 if data[position:position + 2] == b"\x00\x00" else 0
                        results.append(StringCandidate(
                            start, position + terminator, encoding, text, terminator,
                        ))
                position += 2
    return results


def extract_strings(data: bytes, min_length: int = 4) -> list[StringCandidate]:
    """Return textual candidates, retaining overlapping interpretations.

    min_length counts decoded characters. End offsets include a trailing NUL
    when present. Candidates are observations, not proof of a data region.
    """
    if min_length < 1:
        raise ValueError("min_length deve essere almeno 1")
    candidates = _scan_utf8(data, min_length) + _scan_utf16_latin(data, min_length)
    return sorted(candidates, key=lambda item: (item.start, item.end, item.encoding))


def _preview(text: str, width: int = 64) -> str:
    # ASCII escaping prevents control/bidi sequences and console encoding errors.
    value = ascii(text)
    return value if len(value) <= width else value[:width - 3] + "..."


def _hexdump(data: bytes, start: int, end: int, context: int = 8) -> list[str]:
    # Bound display cost for huge strings; the table still reports the full range.
    lo = max(0, start - context)
    hi = min(len(data), end + context, start + 96)
    lines = []
    for offset in range(lo, hi, 16):
        chunk = data[offset:min(offset + 16, hi)]
        hex_bytes = " ".join(f"{byte:02X}" for byte in chunk)
        printable = "".join(chr(byte) if 0x20 <= byte <= 0x7E else "." for byte in chunk)
        lines.append(f"    {offset:08X}  {hex_bytes:<47}  |{printable}|")
    if hi < end:
        lines.append(f"    ... altri {end - hi} byte del candidato non visualizzati")
    return lines


def render_report(
    data: bytes,
    candidates: list[StringCandidate],
    filename: str,
    *,
    limit: int = 100,
    show_hex: bool = False,
) -> str:
    if limit < 0:
        raise ValueError("limit non puo' essere negativo")
    lines = [
        "INVENTARIO DI STRINGHE CANDIDATE",
        "=" * 100,
        f"File: {_preview(filename, 160)}",
        f"Dimensione: {len(data)} byte (0x{len(data):X}) | Candidati: {len(candidates)}",
        "Offset nel file; FINE esclusa. BYTE include il terminatore NUL, se presente.",
        "Sono indizi testuali, non regioni dati accertate. Possibili falsi positivi e sovrapposizioni.",
        "UTF-16: repertorio latino U+0020..U+024F; nessuna analisi del flusso di esecuzione.",
        "",
    ]
    if not candidates:
        lines.append("Nessuna stringa candidata con i criteri selezionati.")
        return "\n".join(lines)
    lines += [
        "  #  INIZIO      FINE        BYTE  CODIFICA   NUL  TESTO",
        "-" * 100,
    ]
    shown = candidates if limit == 0 else candidates[:limit]
    for number, candidate in enumerate(shown, 1):
        nul = "si" if candidate.terminator_size else "no"
        lines.append(
            f"{number:3}  0x{candidate.start:08X}  0x{candidate.end:08X}  "
            f"{candidate.byte_length:4}  {candidate.encoding:<9}  {nul:<3}  "
            f"{_preview(candidate.text)}"
        )
        if show_hex:
            lines.extend(_hexdump(data, candidate.start, candidate.end))
    if len(shown) < len(candidates):
        lines.append(f"\nAltri {len(candidates) - len(shown)} candidati. Usa --limit 0 per mostrarli tutti.")
    return "\n".join(lines)


def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("deve essere almeno 1")
    return number


def _nonnegative(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("non puo' essere negativo")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventario statico di stringhe candidate; non distingue con certezza codice e dati.",
    )
    parser.add_argument("file", type=Path, help="file binario da leggere")
    parser.add_argument("--min-length", type=_positive, default=4, metavar="N",
                        help="numero minimo di caratteri (default: 4)")
    parser.add_argument("--limit", type=_nonnegative, default=100, metavar="N",
                        help="massimo di risultati stampati, 0 = tutti (default: 100)")
    parser.add_argument("--hex", action="store_true", help="mostra anche il contesto esadecimale")
    args = parser.parse_args(argv)
    try:
        data = args.file.read_bytes()
    except OSError as error:
        print(f"Errore nella lettura di {ascii(str(args.file))}: {ascii(str(error))}", file=sys.stderr)
        return 1
    print(render_report(data, extract_strings(data, args.min_length), str(args.file),
                        limit=args.limit, show_hex=args.hex))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
