"""Tests on inert byte fixtures; no binary input is executed."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from inspect_strings import StringCandidate, extract_strings, main, render_report


class StringInventoryTests(unittest.TestCase):
    def test_ascii_offsets_include_null(self):
        data = b"\xff\x00Hello, world!\x00\xff"
        self.assertIn(StringCandidate(2, 16, "ASCII", "Hello, world!", 1),
                      extract_strings(data))

    def test_utf8_length_counts_characters_not_bytes(self):
        text = "citt\u00e0 \u6771\u4eac"
        encoded = text.encode("utf-8")
        data = b"\xff" + encoded + b"\x00"
        self.assertIn(StringCandidate(1, len(data), "UTF-8", text, 1),
                      extract_strings(data))
        self.assertEqual(extract_strings("\u00e8\u00e9".encode("utf-8"), min_length=3), [])

    def test_invalid_utf8_and_truncated_tail(self):
        candidates = extract_strings(b"ABCD\xffEFGH\xe2\x82")
        ascii_candidates = [candidate for candidate in candidates if candidate.encoding == "ASCII"]
        self.assertEqual(ascii_candidates, [StringCandidate(0, 4, "ASCII", "ABCD"),
                                            StringCandidate(5, 9, "ASCII", "EFGH")])

    def test_utf16_byte_orders_and_unaligned_starts(self):
        for codec, label in (("utf-16-le", "UTF-16LE"), ("utf-16-be", "UTF-16BE")):
            for alignment in (0, 1):
                with self.subTest(codec=codec, alignment=alignment):
                    text = "Caff\u00e8"
                    data = b"\xff" * alignment + text.encode(codec) + b"\x00\x00"
                    self.assertIn(StringCandidate(alignment, len(data), label, text, 2),
                                  extract_strings(data))

    def test_end_of_file_is_not_a_terminator(self):
        self.assertIn(StringCandidate(1, 5, "ASCII", "test"), extract_strings(b"\x00test"))
        self.assertIn(StringCandidate(0, 8, "UTF-16LE", "test"),
                      extract_strings("test".encode("utf-16-le")))

    def test_utf16_half_terminator_is_not_a_terminator(self):
        self.assertIn(StringCandidate(0, 8, "UTF-16LE", "test"),
                      extract_strings("test".encode("utf-16-le") + b"\x00"))

    def test_empty_and_whitespace_only(self):
        for data in (b"", b"\x00\xff\x00", b"    \x00", "    ".encode("utf-16-le")):
            with self.subTest(data=data):
                self.assertEqual(extract_strings(data), [])

    def test_report_escapes_text_and_limits_results(self):
        data = b"hello\x00world\x00"
        report = render_report(data, extract_strings(data), "bad\x1b[31m.bin", limit=1, show_hex=True)
        self.assertNotIn("\x1b", report)
        self.assertIn("\\x1b", report)
        self.assertIn("Altri 1 candidati", report)
        self.assertIn("68 65 6C 6C 6F", report)
        self.assertIn("FINE esclusa", report)

    def test_hex_preview_is_bounded(self):
        data = b"A" * 10000
        report = render_report(data, extract_strings(data), "large.bin", show_hex=True)
        self.assertLess(len(report), 2500)
        self.assertIn("non visualizzati", report)

    def test_cli_only_reads_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bin"
            data = b"\x00Example text\x00"
            path.write_bytes(data)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main([str(path), "--hex"])
            self.assertEqual(result, 0)
            self.assertIn("Example text", output.getvalue())
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_missing_file_has_clear_error(self):
        with tempfile.TemporaryDirectory() as directory:
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                result = main([str(Path(directory) / "missing.bin")])
            self.assertEqual(result, 1)
            self.assertIn("Errore nella lettura", error.getvalue())

    def test_minimum_must_be_positive(self):
        with self.assertRaises(ValueError):
            extract_strings(b"test", min_length=0)


if __name__ == "__main__":
    unittest.main()
