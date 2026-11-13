"""Unit tests for the LLM token/cost statistics."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from llm_stats import (APICall, AttemptRecord, RunStats, estimate_cost,
                       is_peak, model_version, price_for, usage_numbers)


class LLMStatsTests(unittest.TestCase):
    def test_usage_parsing(self):
        usage = usage_numbers({
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
            "prompt_cache_hit_tokens": 30,
            "prompt_cache_miss_tokens": 70,
            "completion_tokens_details": {"reasoning_tokens": 10},
        })
        self.assertEqual((usage.prompt, usage.completion, usage.total),
                         (100, 20, 120))
        self.assertEqual((usage.hit, usage.miss, usage.reasoning),
                         (30, 70, 10))
        self.assertAlmostEqual(usage.cache_ratio, 0.3)
        self.assertAlmostEqual(usage.reasoning_ratio, 0.5)

    def test_flash_off_peak_cost(self):
        at = datetime(2026, 11, 12, 21, 18, tzinfo=timezone.utc)
        self.assertFalse(is_peak(at))
        usage = usage_numbers({
            "prompt_tokens": 3545,
            "completion_tokens": 12090,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 3545,
        })
        cost = estimate_cost(usage, "deepseek-flash", at)
        self.assertIsNotNone(cost)
        self.assertAlmostEqual(cost.total, 0.00778575, places=9)
        self.assertEqual(cost.label, "off-peak")

    def test_flash_peak_cost(self):
        at = datetime(2026, 11, 12, 2, 0, tzinfo=timezone.utc)
        self.assertTrue(is_peak(at))
        usage = usage_numbers({
            "prompt_tokens": 3545,
            "completion_tokens": 12090,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 3545,
        })
        cost = estimate_cost(usage, "deepseek-flash", at)
        self.assertAlmostEqual(cost.total, 0.0155715, places=9)
        self.assertEqual(cost.label, "peak")

    def test_cache_hit_is_cheaper(self):
        at = datetime(2026, 11, 12, 21, 18, tzinfo=timezone.utc)
        usage = usage_numbers({
            "prompt_tokens": 1000,
            "completion_tokens": 0,
            "prompt_cache_hit_tokens": 1000,
            "prompt_cache_miss_tokens": 0,
        })
        cost = estimate_cost(usage, "deepseek-flash", at)
        self.assertAlmostEqual(cost.total, 0.000003, places=12)

    def test_weekend_is_off_peak(self):
        saturday = datetime(2026, 11, 14, 2, 0, tzinfo=timezone.utc)
        self.assertFalse(is_peak(saturday))

    def test_unknown_model_has_no_price(self):
        at = datetime(2026, 11, 12, 21, 18, tzinfo=timezone.utc)
        self.assertIsNone(price_for("not-a-model", False))
        self.assertEqual(model_version("deepseek-flash"),
                         "DeepSeek-V4.1-Flash-1017")

    def test_run_summary_and_json(self):
        at = datetime(2026, 11, 12, 21, 18, tzinfo=timezone.utc)
        stats = RunStats("deepseek-flash", "eq", "x64", started_at=at)
        stats.add_api_call(APICall(
            attempt=1, started_at=at, seconds=12.5,
            usage={
                "prompt_tokens": 3545,
                "completion_tokens": 12090,
                "total_tokens": 15635,
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": 3545,
                "completion_tokens_details": {"reasoning_tokens": 11800},
            },
            finish_reason="stop", content_chars=4200))
        stats.add_attempt(AttemptRecord(
            attempt=1, started_at=at, seconds=14.0, api_seconds=12.5,
            response_chars=4200, accepted=True, similarity=0.93,
            code_bytes=341, data_bytes=39, instructions=131))
        stats.finished_at = at + timedelta(seconds=15.0)
        stats.finish(True)

        text = stats.summary()
        self.assertIn("15,635", text)
        self.assertIn("$0.007786", text)
        self.assertIn("DeepSeek-V4.1-Flash-1017", text)
        self.assertIn("similarity 0.93", text)
        self.assertIn("12.5s", text)

        handle = tempfile.NamedTemporaryFile("w", suffix=".json",
                                             delete=False)
        handle.close()
        try:
            stats.write_json(handle.name)
            with open(handle.name, encoding="utf-8") as source:
                data = json.load(source)
        finally:
            os.unlink(handle.name)
        self.assertEqual(data["model"], "deepseek-flash")
        self.assertEqual(data["usage"]["total_tokens"], 15635)
        self.assertAlmostEqual(data["cost_usd"]["total"], 0.00778575,
                               places=9)
        self.assertEqual(data["payload"]["code_bytes"], 341)
        self.assertIn("attempt_details", data)
        self.assertIn("api_call_details", data)
        self.assertEqual(data["api_call_details"][0]["usage"]["prompt_tokens"],
                         3545)
        self.assertEqual(data["api_call_details"][0]["generation_attempt"],
                         0)

    def test_eur_rate_is_optional(self):
        at = datetime(2026, 11, 12, 21, 18, tzinfo=timezone.utc)
        stats = RunStats("deepseek-flash", "eq", "x64", started_at=at)
        stats.add_api_call(APICall(
            attempt=1, started_at=at, seconds=1.0,
            usage={"prompt_tokens": 1000, "completion_tokens": 1000,
                   "prompt_cache_hit_tokens": 0,
                   "prompt_cache_miss_tokens": 1000}))
        stats.finished_at = at + timedelta(seconds=2.0)
        stats.finish(True)
        old = os.environ.get("ZONE_LLM_EUR_RATE")
        try:
            os.environ["ZONE_LLM_EUR_RATE"] = "0.92"
            self.assertIn("approx EUR", stats.summary())
        finally:
            if old is None:
                os.environ.pop("ZONE_LLM_EUR_RATE", None)
            else:
                os.environ["ZONE_LLM_EUR_RATE"] = old


if __name__ == "__main__":
    unittest.main(verbosity=2)
