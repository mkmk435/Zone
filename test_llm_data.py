"""Offline tests for LLM-based data classification."""

import json
import os
import tempfile
import unittest

from keystone import Ks, KS_ARCH_X86, KS_MODE_64

from llm_data import (DataError, build_data_prompt, parse_sections, run_data)
from llm_technique import LLMOptions
from pobf import Zone

KS = Ks(KS_ARCH_X86, KS_MODE_64)

PAYLOAD_SOURCE = """
_start:
    lea rsi, [rip + msg]
    mov eax, 1
    ret
msg:
    .byte 0x68, 0x65, 0x6c, 0x6c, 0x6f, 0x00
"""


class LLMDataTests(unittest.TestCase):
    def _payload(self):
        encoding, _ = KS.asm(PAYLOAD_SOURCE, 0)
        raw = bytes(encoding)
        handle = tempfile.NamedTemporaryFile("wb", suffix=".bin",
                                             delete=False)
        handle.write(raw)
        handle.close()
        return raw, handle.name

    def test_prompt_shots(self):
        raw = b"\x90" * 8
        none = build_data_prompt(raw, "x64", shots=0)
        one = build_data_prompt(raw, "x64", shots=1)
        two = build_data_prompt(raw, "x64", shots=2)
        self.assertNotIn("--- example", none)
        self.assertEqual(one.count("--- example"), 1)
        self.assertEqual(two.count("--- example"), 2)

    def test_parse_sections_and_errors(self):
        sections = parse_sections(json.dumps({
            "sections": [
                {"offset": "0x0d", "length": "0x6", "kind": "ascii",
                 "text": "hello"},
            ],
        }), 32)
        self.assertEqual(sections[0]["offset"], 13)
        self.assertEqual(sections[0]["length"], 6)

        with self.assertRaises(DataError):
            parse_sections(json.dumps({
                "sections": [
                    {"offset": 10, "length": 8},
                    {"offset": 15, "length": 4},
                ],
            }), 32)
        with self.assertRaises(DataError):
            parse_sections(json.dumps({
                "sections": [{"offset": 30, "length": 8}],
            }), 32)

    def test_end_instead_of_length(self):
        sections = parse_sections(json.dumps({
            "sections": [{"offset": 4, "end": 10, "kind": "table"}],
        }), 32)
        self.assertEqual(sections[0]["length"], 6)

    def test_mock_classification_and_extraction(self):
        raw, path = self._payload()
        response = tempfile.NamedTemporaryFile("w", suffix=".json",
                                               delete=False)
        response.write(json.dumps({
            "sections": [{"offset": 13, "length": 6, "kind": "ascii",
                          "text": "hello"}],
        }))
        response.close()
        try:
            options = LLMOptions(technique="data", arch="x64",
                                 mock_response=response.name, retries=1)
            result = run_data(lambda: Zone(path), raw, "x64", options)
            self.assertEqual(result.data_bytes, 6)
            self.assertTrue(result.zone.extracted_data)
            self.assertIn(b"hello\x00", result.zone.final_data_blob)
            self.assertEqual(result.stats.technique, "data")
            self.assertIn("extraction: ok", result.stats.summary())
            output = tempfile.NamedTemporaryFile("wb", suffix=".bin",
                                                  delete=False)
            output.close()
            try:
                result.zone.write_file(output.name)
                with open(output.name, "rb") as handle:
                    written = handle.read()
                self.assertIn(b"hello\x00", written)
            finally:
                os.unlink(output.name)
        finally:
            os.unlink(path)
            os.unlink(response.name)

    def test_empty_sections_with_gaps_is_rejected(self):
        # A payload with an undecodable tail: returning no sections must be
        # rejected instead of silently leaving data in the code stream.
        raw = b"\x90\x90\x90\x90\x48\x8d"

        class FakeZone:
            sweep_coverage = 4
            instructions = []

        response = tempfile.NamedTemporaryFile("w", suffix=".json",
                                               delete=False)
        response.write('{"sections":[]}')
        response.close()
        try:
            options = LLMOptions(technique="data", arch="x64",
                                 mock_response=response.name, retries=1)
            with self.assertRaises(Exception):
                run_data(lambda: FakeZone(), raw, "x64", options)
        finally:
            os.unlink(response.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
