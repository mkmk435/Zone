"""Token, time and cost statistics for the LLM morphing mode.

Prices come from the DeepSeek pricing page (per 1M tokens, USD):

    https://api-docs.deepseek.com/quick_start/pricing/

The table is a snapshot and can change.  The rates can be overridden from the
environment with ``ZONE_LLM_PRICE_HIT``, ``ZONE_LLM_PRICE_MISS`` and
``ZONE_LLM_PRICE_OUTPUT`` (USD per 1M tokens, all three optional).  The
peak/off-peak split follows the published UTC schedule; Chinese public
holidays are not modelled, so a holiday run is reported as peak/off-peak by
the weekday/hour rule only.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

PRICING_URL = "https://api-docs.deepseek.com/quick_start/pricing/"
PEAK_RANGES_UTC = ((1, 4), (6, 10))


@dataclass(frozen=True)
class Price:
    """USD per 1M tokens."""

    hit: float
    miss: float
    output: float


@dataclass(frozen=True)
class ModelPrice:
    version: str
    off_peak: Price
    peak: Price


MODEL_PRICES: Dict[str, ModelPrice] = {
    "deepseek-flash": ModelPrice(
        version="DeepSeek-V4.1-Flash-1017",
        off_peak=Price(hit=0.003, miss=0.15, output=0.6),
        peak=Price(hit=0.006, miss=0.3, output=1.2),
    ),
    "deepseek-v4-pro": ModelPrice(
        version="DeepSeek-V4-Pro-0813",
        off_peak=Price(hit=0.022, miss=0.66, output=1.98),
        peak=Price(hit=0.044, miss=1.32, output=3.96),
    ),
}

MODEL_ALIASES = {
    "deepseek-v4.1-flash": "deepseek-flash",
    "deepseek-v4.1-flash-1017": "deepseek-flash",
    "deepseek-v4-flash": "deepseek-flash",
    "deepseek-v4-flash-vision-exp": "deepseek-flash",
}


def normalise_model(model: str) -> str:
    name = (model or "").strip().lower()
    if "/" in name:
        name = name.rsplit("/", 1)[-1]
    if ":" in name:
        name = name.split(":", 1)[0]
    return MODEL_ALIASES.get(name, name)


def model_version(model: str) -> str:
    price = MODEL_PRICES.get(normalise_model(model))
    return price.version if price else "unknown model"


def is_peak(at: datetime) -> bool:
    """True inside the published peak windows (UTC, Mon-Fri)."""
    if at.tzinfo is None:
        at = at.replace(tzinfo=timezone.utc)
    at = at.astimezone(timezone.utc)
    if at.weekday() >= 5:          # Saturday/Sunday are always off-peak
        return False
    return any(start <= at.hour < end for start, end in PEAK_RANGES_UTC)


def _custom_price(base: Price) -> Optional[Price]:
    values = [os.environ.get(f"ZONE_LLM_PRICE_{name}")
              for name in ("HIT", "MISS", "OUTPUT")]
    if not any(value and value.strip() for value in values):
        return None
    parsed = []
    for value, fallback in zip(values, (base.hit, base.miss, base.output)):
        try:
            parsed.append(float(value) if value and value.strip() else fallback)
        except ValueError:
            parsed.append(fallback)
    return Price(*parsed)


def price_for(model: str, peak: bool) -> Optional[tuple]:
    """Return ``(Price, label, version)`` or ``None`` for unknown models."""
    name = normalise_model(model)
    entry = MODEL_PRICES.get(name)
    if entry is None:
        base = Price(hit=0.0, miss=0.0, output=0.0)
        custom = _custom_price(base)
        if custom is None:
            return None
        return custom, "custom", "unknown model"
    base = entry.peak if peak else entry.off_peak
    custom = _custom_price(base)
    if custom is not None:
        return custom, "custom", entry.version
    return base, ("peak" if peak else "off-peak"), entry.version


@dataclass
class Usage:
    prompt: int = 0
    completion: int = 0
    total: int = 0
    hit: int = 0
    miss: int = 0
    reasoning: int = 0

    @property
    def cache_ratio(self) -> float:
        counted = self.hit + self.miss
        return (self.hit / counted) if counted else 0.0

    @property
    def reasoning_ratio(self) -> float:
        return (self.reasoning / self.completion) if self.completion else 0.0

    def as_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt,
            "completion_tokens": self.completion,
            "total_tokens": self.total,
            "cache_hit_tokens": self.hit,
            "cache_miss_tokens": self.miss,
            "reasoning_tokens": self.reasoning,
        }


def usage_numbers(usage: Optional[dict]) -> Usage:
    usage = usage or {}
    prompt = int(usage.get("prompt_tokens")
                 or usage.get("input_tokens") or 0)
    completion = int(usage.get("completion_tokens")
                     or usage.get("output_tokens") or 0)
    total = int(usage.get("total_tokens") or (prompt + completion))
    hit = int(usage.get("prompt_cache_hit_tokens") or 0)
    miss = int(usage.get("prompt_cache_miss_tokens") or 0)
    prompt_details = usage.get("prompt_tokens_details") or {}
    if not hit:
        hit = int(prompt_details.get("cached_tokens") or 0)
    if hit == 0 and miss == 0 and prompt:
        miss = prompt
    elif miss == 0 and prompt > hit:
        miss = prompt - hit
    completion_details = usage.get("completion_tokens_details") or {}
    reasoning = int(completion_details.get("reasoning_tokens") or 0)
    return Usage(prompt=prompt, completion=completion, total=total,
                 hit=hit, miss=miss, reasoning=reasoning)


@dataclass
class Cost:
    hit_cost: float
    miss_cost: float
    output_cost: float
    total: float
    peak: bool
    label: str


def estimate_cost(usage: Usage, model: str,
                  at: datetime) -> Optional[Cost]:
    priced = price_for(model, is_peak(at))
    if priced is None:
        return None
    price, label, _version = priced
    hit_cost = usage.hit / 1_000_000.0 * price.hit
    miss_cost = usage.miss / 1_000_000.0 * price.miss
    output_cost = usage.completion / 1_000_000.0 * price.output
    return Cost(hit_cost=hit_cost, miss_cost=miss_cost,
                output_cost=output_cost,
                total=hit_cost + miss_cost + output_cost,
                peak=is_peak(at), label=label)


@dataclass
class APICall:
    attempt: int
    started_at: datetime
    seconds: float
    usage: dict = field(default_factory=dict)
    finish_reason: Optional[str] = None
    content_chars: int = 0
    error: Optional[str] = None
    generation_attempt: int = 0
    usage_obj: Optional[Usage] = None
    cost: Optional[Cost] = None


@dataclass
class AttemptRecord:
    attempt: int
    started_at: datetime
    seconds: float
    api_seconds: float
    response_chars: int
    accepted: bool
    error: Optional[str] = None
    similarity: float = 0.0
    code_bytes: int = 0
    data_bytes: int = 0
    instructions: int = 0


class RunStats:
    """Aggregate statistics for one ``--llm`` invocation."""

    def __init__(self, model: str, technique: str, arch: str,
                 started_at: Optional[datetime] = None):
        self.model = model
        self.technique = technique
        self.arch = arch
        self.started_at = started_at or datetime.now(timezone.utc)
        self.finished_at: Optional[datetime] = None
        self.api_calls: List[APICall] = []
        self.attempts: List[AttemptRecord] = []
        self.errors: List[str] = []
        self.ok = False
        self.error: Optional[str] = None

    # -- collection -----------------------------------------------------
    def add_api_call(self, call: APICall) -> None:
        call.usage_obj = usage_numbers(call.usage)
        if call.usage_obj.prompt or call.usage_obj.completion:
            call.cost = estimate_cost(call.usage_obj, self.model,
                                      call.started_at)
        self.api_calls.append(call)

    def add_attempt(self, record: AttemptRecord) -> None:
        self.attempts.append(record)
        if not record.accepted and record.error:
            self.errors.append(record.error)

    def finish(self, ok: bool, error: Optional[str] = None) -> None:
        self.ok = ok
        self.error = error
        self.finished_at = datetime.now(timezone.utc)

    # -- aggregate ------------------------------------------------------
    @property
    def wall_seconds(self) -> float:
        end = self.finished_at or datetime.now(timezone.utc)
        return max(0.0, (end - self.started_at).total_seconds())

    @property
    def api_seconds(self) -> float:
        return sum(call.seconds for call in self.api_calls)

    @property
    def local_seconds(self) -> float:
        return max(0.0, self.wall_seconds - self.api_seconds)

    @property
    def usage(self) -> Usage:
        return self.usage_since(0)

    def usage_since(self, index: int) -> Usage:
        totals = Usage()
        for call in self.api_calls[index:]:
            if call.usage_obj is None:
                continue
            totals.prompt += call.usage_obj.prompt
            totals.completion += call.usage_obj.completion
            totals.total += call.usage_obj.total
            totals.hit += call.usage_obj.hit
            totals.miss += call.usage_obj.miss
            totals.reasoning += call.usage_obj.reasoning
        return totals

    def _cost_for(self, calls: List[APICall]) -> Optional[Cost]:
        priced = [call.cost for call in calls if call.cost is not None]
        if not priced:
            return None
        peak_calls = sum(1 for call in calls if call.cost and call.cost.peak)
        labels = {call.cost.label for call in calls if call.cost}
        label = labels.pop() if len(labels) == 1 else "mixed"
        return Cost(
            hit_cost=sum(cost.hit_cost for cost in priced),
            miss_cost=sum(cost.miss_cost for cost in priced),
            output_cost=sum(cost.output_cost for cost in priced),
            total=sum(cost.total for cost in priced),
            peak=peak_calls > 0,
            label=label,
        )

    @property
    def cost(self) -> Optional[Cost]:
        return self._cost_for(self.api_calls)

    def cost_since(self, index: int) -> Optional[Cost]:
        return self._cost_for(self.api_calls[index:])

    @property
    def peak_calls(self) -> int:
        return sum(1 for call in self.api_calls if call.cost and call.cost.peak)

    @property
    def offpeak_calls(self) -> int:
        return sum(1 for call in self.api_calls
                   if call.cost and not call.cost.peak)

    @property
    def accepted_attempt(self) -> Optional[AttemptRecord]:
        for record in reversed(self.attempts):
            if record.accepted:
                return record
        return None

    def to_dict(self) -> dict:
        usage = self.usage
        cost = self.cost
        accepted = self.accepted_attempt
        return {
            "model": self.model,
            "model_version": model_version(self.model),
            "technique": self.technique,
            "arch": self.arch,
            "started_at": self.started_at.isoformat(),
            "finished_at": (self.finished_at.isoformat()
                            if self.finished_at else None),
            "ok": self.ok,
            "error": self.error,
            "timing": {
                "wall_seconds": round(self.wall_seconds, 3),
                "api_seconds": round(self.api_seconds, 3),
                "local_seconds": round(self.local_seconds, 3),
            },
            "attempts": len(self.attempts),
            "api_calls": len(self.api_calls),
            "rejected_attempts": sum(1 for record in self.attempts
                                     if not record.accepted),
            "attempt_details": [
                {
                    "attempt": record.attempt,
                    "seconds": round(record.seconds, 3),
                    "api_seconds": round(record.api_seconds, 3),
                    "accepted": record.accepted,
                    "similarity": round(record.similarity, 4),
                    "code_bytes": record.code_bytes,
                    "data_bytes": record.data_bytes,
                    "instructions": record.instructions,
                    "error": record.error,
                }
                for record in self.attempts
            ],
            "api_call_details": [
                {
                    "attempt": call.attempt,
                    "generation_attempt": call.generation_attempt,
                    "started_at": call.started_at.isoformat(),
                    "seconds": round(call.seconds, 3),
                    "finish_reason": call.finish_reason,
                    "content_chars": call.content_chars,
                    "usage": (call.usage_obj.as_dict()
                              if call.usage_obj is not None else {}),
                    "cost_usd": (round(call.cost.total, 9)
                                 if call.cost is not None else None),
                    "error": call.error,
                }
                for call in self.api_calls
            ],
            "usage": usage.as_dict(),
            "cost_usd": (None if cost is None else {
                "total": round(cost.total, 9),
                "cache_hit": round(cost.hit_cost, 9),
                "cache_miss": round(cost.miss_cost, 9),
                "output": round(cost.output_cost, 9),
                "peak": cost.peak,
                "rate": cost.label,
            }),
            "peak_calls": self.peak_calls,
            "offpeak_calls": self.offpeak_calls,
            "cache_hit_ratio": round(usage.cache_ratio, 4),
            "reasoning_ratio": round(usage.reasoning_ratio, 4),
            "payload": {
                "code_bytes": accepted.code_bytes if accepted else 0,
                "data_bytes": accepted.data_bytes if accepted else 0,
                "instructions": accepted.instructions if accepted else 0,
                "similarity": round(accepted.similarity, 4) if accepted else 0.0,
            },
            "errors": self.errors[-10:],
            "pricing_url": PRICING_URL,
            "pricing_note": "USD per 1M tokens; peak/off-peak by UTC "
                            "schedule, Chinese holidays not modelled",
        }

    def write_json(self, path: str) -> None:
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(self.to_dict(), handle, indent=2)
            handle.write("\n")

    # -- formatting -----------------------------------------------------
    @staticmethod
    def _int(value: int) -> str:
        return f"{value:,}"

    @staticmethod
    def _seconds(value: float) -> str:
        if value < 60:
            return f"{value:.1f}s"
        return f"{int(value // 60)}m {value % 60:04.1f}s"

    @staticmethod
    def _usd(value: float) -> str:
        if value and value < 0.000001:
            return "<$0.000001"
        return f"${value:.6f}"

    @staticmethod
    def eur_rate() -> Optional[float]:
        raw = os.environ.get("ZONE_LLM_EUR_RATE", "").strip()
        if not raw:
            return None
        try:
            rate = float(raw)
        except ValueError:
            return None
        return rate if rate > 0 else None

    def summary(self) -> str:
        usage = self.usage
        cost = self.cost
        accepted = self.accepted_attempt
        lines = ["=" * 68, "[llm] run statistics"]
        lines.append(
            f"  model:      {self.model} ({model_version(self.model)})")
        lines.append(f"  technique:  {self.technique} ({self.arch})")
        lines.append(
            f"  attempts:   {len(self.attempts)} "
            f"({len(self.api_calls)} API call(s), "
            f"{sum(1 for r in self.attempts if not r.accepted)} rejected)")
        lines.append(
            f"  time:       {self._seconds(self.wall_seconds)} total "
            f"(API {self._seconds(self.api_seconds)}, "
            f"local {self._seconds(self.local_seconds)})")
        for record in self.attempts:
            status = "ok" if record.accepted else "rejected"
            error_text = (record.error or "").replace("\n", " ")
            if len(error_text) > 60:
                error_text = error_text[:57] + "..."
            detail = (f", similarity {record.similarity:.2f}"
                      if record.accepted else
                      f", {error_text}" if error_text else "")
            lines.append(
                f"  attempt {record.attempt}: {record.seconds:.1f}s, "
                f"{status}{detail}")

        lines.append(
            f"  tokens:     {self._int(usage.total)} total = "
            f"{self._int(usage.prompt)} input + "
            f"{self._int(usage.completion)} output")
        lines.append(
            f"              input: {self._int(usage.hit)} cache hit + "
            f"{self._int(usage.miss)} cache miss "
            f"({usage.cache_ratio:.1%} hit)")
        lines.append(
            f"              output: {self._int(usage.completion)} "
            f"(reasoning {self._int(usage.reasoning)}, "
            f"{usage.reasoning_ratio:.1%})")
        if self.api_seconds > 0:
            lines.append(
                f"  throughput: {usage.completion / self.api_seconds:,.1f} "
                "output tokens/s (API time)")

        if cost is None:
            if price_for(self.model, False) is None:
                lines.append(
                    f"  cost:       n/a (no price table for {self.model!r})")
            else:
                lines.append(
                    "  cost:       n/a (no API usage recorded)")
        else:
            rate_label = cost.label
            if rate_label == "mixed":
                rate_label = (f"mixed: {self.peak_calls} peak / "
                              f"{self.offpeak_calls} off-peak")
            lines.append(
                f"  cost:       {self._usd(cost.total)} USD "
                f"({rate_label})")
            lines.append(
                f"              input {self._usd(cost.hit_cost + cost.miss_cost)}"
                f" (hit {self._usd(cost.hit_cost)}, "
                f"miss {self._usd(cost.miss_cost)}) + "
                f"output {self._usd(cost.output_cost)}")
            eur = self.eur_rate()
            if eur is not None:
                lines.append(
                    f"              approx EUR {cost.total * eur:.6f} "
                    f"(rate {eur:g})")
            lines.append(
                "              prices: DeepSeek official USD/1M tokens; "
                "peak/off-peak UTC, holidays not modelled")

        if accepted:
            lines.append(
                f"  payload:    {accepted.code_bytes} code + "
                f"{accepted.data_bytes} data bytes, "
                f"{accepted.instructions} instructions")
            lines.append(
                f"  validation: {'ok' if self.ok else 'failed'}, "
                f"similarity {accepted.similarity:.2f}")
        if self.errors:
            lines.append("  errors:     " + " | ".join(self.errors[-3:]))
        lines.append("=" * 68)
        return "\n".join(lines)
