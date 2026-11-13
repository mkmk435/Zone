"""Offline tests for the LLM morphing mode.

They do not call the network.  A mock response is used to drive the same
canonicalise -> prompt -> assemble -> validate pipeline that the DeepSeek
client uses, and the resulting payloads are executed on the real CPU through
``test_asm_wrap.Runner``.

Run with:  python test_llm_technique.py
"""

import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from keystone import Ks, KS_ARCH_X86, KS_MODE_64

from llm_payload import (LLMPayloadError, assemble, canonicalize, validate)
from llm_technique import (DeepSeekClient, LLMConfigError, LLMOptions,
                           TECHNIQUES, build_user_prompt, run,
                           resolve_api_key)
from test_asm_wrap import Runner

KS = Ks(KS_ARCH_X86, KS_MODE_64)


def assemble_input(source):
    encoding, _ = KS.asm(source, 0)
    return bytes(encoding)


PROGRAMMES = {
    "straight": """
        mov eax, 0x1234
        add eax, 5
        sub eax, 0x34
        mov dword ptr [rcx], eax
        ret
    """,
    "flags": """
        xor eax, eax
        mov edx, 4
    loop_head:
        add eax, edx
        dec edx
        jnz loop_head
        mov dword ptr [rcx], eax
        ret
    """,
    "call": """
        mov eax, 7
        call helper
        mov dword ptr [rcx], eax
        ret
    helper:
        add eax, 5
        ret
    """,
}


class LLMPayloadTests(unittest.TestCase):
    def test_roundtrip_executes_like_the_original(self):
        runner = Runner()
        for name, source in PROGRAMMES.items():
            code = assemble_input(source)
            expected = runner(code)
            canonical = canonicalize(code, b"", "x64")
            assembled = assemble(canonical.source, canonical)
            report = validate(assembled, canonical, technique="eq",
                              min_similarity=None)
            self.assertTrue(report.ok, f"{name}: {report.errors}")
            self.assertEqual(runner(assembled.payload), expected,
                             f"{name}: round-trip changed the result")

    def test_equal_substitution_mock(self):
        source = PROGRAMMES["straight"]
        code = assemble_input(source)
        canonical = canonicalize(code, b"", "x64")
        morphed = """
```asm
_start:
L_0:
    mov eax, 0x1234
    test eax, eax
    sub eax, -5
    add eax, -0x34
    mov dword ptr [rcx], eax
    ret
```
"""
        with tempfile.NamedTemporaryFile("w", suffix=".txt",
                                         delete=False) as handle:
            handle.write(morphed)
            path = handle.name
        try:
            options = LLMOptions(technique="eq", arch="x64",
                                 mock_response=path)
            result = run(canonical, options)
        finally:
            os.unlink(path)
        runner = Runner()
        self.assertEqual(runner(result.payload), runner(code))
        self.assertTrue(result.report.ok)
        self.assertIsNotNone(result.stats)
        self.assertIn("run statistics", result.stats.summary())

    def test_nop_and_bcf_mocks(self):
        name = "straight"
        code = assemble_input(PROGRAMMES[name])
        canonical = canonicalize(code, b"", "x64")
        expected = Runner()(code)

        nop_source = canonical.source.replace(
            "    mov eax, 0x1234",
            "    nop\n    mov eax, 0x1234")
        bcf_source = canonical.source.replace(
            "    mov eax, 0x1234",
            "    pushfq\n"
            "    push rax\n"
            "    xor eax, eax\n"
            "    jnz bogus_1\n"
            "    jmp real_1\n"
            "bogus_1:\n"
            "    nop\n"
            "real_1:\n"
            "    pop rax\n"
            "    popfq\n"
            "    mov eax, 0x1234")
        for technique, text in (("nop", nop_source), ("bcf", bcf_source)):
            with tempfile.NamedTemporaryFile("w", suffix=".txt",
                                             delete=False) as handle:
                handle.write(text)
                path = handle.name
            try:
                result = run(canonical, LLMOptions(
                    technique=technique, arch="x64", mock_response=path))
            finally:
                os.unlink(path)
            self.assertTrue(result.report.ok,
                            f"{technique}: {result.report.errors}")
            self.assertEqual(Runner()(result.payload), expected,
                             f"{technique}: execution changed")

    def test_block_permutation_mock(self):
        code = assemble_input(PROGRAMMES["straight"])
        canonical = canonicalize(code, b"", "x64")
        morphed = """
```asm
_start:
L_0:
    mov eax, 0x1234
    jmp block_b
block_c:
    mov dword ptr [rcx], eax
    ret
block_b:
    add eax, 5
    jmp block_d
block_d:
    sub eax, 0x34
    jmp block_c
```
"""
        with tempfile.NamedTemporaryFile("w", suffix=".txt",
                                         delete=False) as handle:
            handle.write(morphed)
            path = handle.name
        try:
            result = run(canonical, LLMOptions(
                technique="ibp", arch="x64", mock_response=path))
        finally:
            os.unlink(path)
        self.assertTrue(result.report.ok, result.report.errors)
        self.assertEqual(Runner()(result.payload), Runner()(code))

    def test_dropped_instruction_is_rejected(self):
        code = assemble_input(PROGRAMMES["straight"])
        canonical = canonicalize(code, b"", "x64")
        morphed = canonical.source.replace("    add eax, 5\n", "")
        assembled = assemble(morphed, canonical)
        report = validate(assembled, canonical, technique="nop")
        self.assertFalse(report.ok)
        self.assertTrue(any("missing" in error.lower()
                            or "disappeared" in error.lower()
                            for error in report.errors), report.errors)

    def test_extra_return_is_rejected(self):
        code = assemble_input(PROGRAMMES["straight"])
        canonical = canonicalize(code, b"", "x64")
        morphed = canonical.source + "\n    ret"
        assembled = assemble(morphed, canonical)
        report = validate(assembled, canonical, technique="nop")
        self.assertFalse(report.ok)
        self.assertTrue(any("return" in error.lower()
                            for error in report.errors), report.errors)

    def test_missing_getpc_label_is_rejected(self):
        code = assemble_input("""
            _start:
            call getpc_target
            getpc_target:
                pop rbp
                ret
        """)
        canonical = canonicalize(code, b"", "x64")
        self.assertTrue(canonical.ret_labels)
        morphed = canonical.source.replace("RET_5:", "")
        # Remove the label line without touching the instruction.
        assembled = assemble(morphed, canonical)
        report = validate(assembled, canonical, technique="nop")
        self.assertFalse(report.ok)
        self.assertTrue(any("RET_" in error for error in report.errors),
                        report.errors)

    def test_retry_after_invalid_first_answer(self):
        code = assemble_input(PROGRAMMES["straight"])
        canonical = canonicalize(code, b"", "x64")
        first = "```asm\nthis is not assembly\n```"
        second = "```asm\n" + canonical.source + "\n```"
        with tempfile.NamedTemporaryFile("w", suffix=".txt",
                                         delete=False) as handle:
            handle.write(first + "\n---ATTEMPT---\n" + second)
            path = handle.name
        try:
            result = run(canonical, LLMOptions(
                technique="eq", arch="x64", mock_response=path,
                retries=2))
        finally:
            os.unlink(path)
        self.assertEqual(result.attempts, 2)
        self.assertTrue(result.report.ok)

    def test_environment_key(self):
        previous = os.environ.get("DEEPSEEK_API_KEY")
        try:
            os.environ["DEEPSEEK_API_KEY"] = "test-key"
            self.assertEqual(resolve_api_key(prompt=False), "test-key")
            del os.environ["DEEPSEEK_API_KEY"]
            with self.assertRaises(LLMConfigError):
                resolve_api_key(prompt=False)
        finally:
            if previous is None:
                os.environ.pop("DEEPSEEK_API_KEY", None)
            else:
                os.environ["DEEPSEEK_API_KEY"] = previous

    def test_examples_assemble(self):
        for key, spec in TECHNIQUES.items():
            for example in spec.all_examples():
                output = example.split("output:", 1)[1].strip()
                encoding, _ = KS.asm(output, 0)
                self.assertTrue(encoding, key)

    def test_few_shot_count(self):
        code = assemble_input(PROGRAMMES["straight"])
        canonical = canonicalize(code, b"", "x64")
        spec = TECHNIQUES["ibp"]
        none = build_user_prompt(canonical, spec, shots=0)
        one = build_user_prompt(canonical, spec, shots=1)
        two = build_user_prompt(canonical, spec, shots=2)
        self.assertNotIn("--- example", none)
        self.assertEqual(one.count("--- example"), 1)
        self.assertEqual(two.count("--- example"), 2)

    def test_ibp_requires_reorder(self):
        code = assemble_input(PROGRAMMES["straight"])
        canonical = canonicalize(code, b"", "x64")
        # Returning the original listing must be rejected: the order did not
        # change, so IBP was not applied.
        noop = assemble(canonical.source, canonical)
        report = validate(noop, canonical, technique="ibp")
        self.assertFalse(report.ok)
        self.assertTrue(any("did not permute" in error
                            for error in report.errors), report.errors)

        # The first worked example is a valid minimal permutation.
        example = TECHNIQUES["ibp"].all_examples()[0]
        output = example.split("output:", 1)[1].strip()
        # The example's instructions do not match the payload above; build the
        # canonical listing from the example input instead.
        input_text = example.split("input:", 1)[1].split("output:", 1)[0]
        input_code = assemble_input(input_text)
        example_canonical = canonicalize(input_code, b"", "x64")
        permuted = assemble(output, example_canonical)
        report = validate(permuted, example_canonical, technique="ibp")
        self.assertTrue(report.ok, report.errors)

    def test_http_client(self):
        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                captured["body"] = json.loads(
                    self.rfile.read(length).decode("utf-8"))
                captured["auth"] = self.headers.get("Authorization")
                response = json.dumps({
                    "choices": [{
                        "message": {"content": "```asm\n_start:\n nop\n```"},
                        "finish_reason": "stop",
                    }],
                    "usage": {"total_tokens": 3},
                }).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            options = LLMOptions(
                technique="eq", arch="x64", api_key="secret",
                base_url=f"http://127.0.0.1:{server.server_port}/v1",
                model="test-model")
            content, usage = DeepSeekClient(options).chat(
                [{"role": "user", "content": "hello"}])
            self.assertIn("_start:", content)
            self.assertEqual(usage["total_tokens"], 3)
            self.assertEqual(captured["body"]["model"], "test-model")
            self.assertEqual(captured["auth"], "Bearer secret")
            self.assertEqual(captured["body"]["messages"][0]["content"],
                             "hello")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
