"""CPU benchmark for the framing-only prompt builder.

This script is intentionally outside the application path.  It loads a local
causal language model, asks it for a short framing JSON object, and records
cold-load, warm-generation, RSS and optional concurrency metrics.  It never
downloads at request time in production; this benchmark may download the base
model into a cache outside the repository.

Run it in WSL/Linux for /proc RSS measurements, for example:

    HF_HOME=~/pb-bench/hf python ai/framing_benchmark.py \
      --model Qwen/Qwen2.5-0.5B-Instruct --precision fp32 --threads 4 --runs 5

The model and results stay outside Git.  Do not commit weights or generated
datasets.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import platform
import time
from typing import Any

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "ai" / "output" / "framing-benchmark"

SYSTEM = (
    "Bạn là bộ phận xây dựng prompt. Chỉ viết phần mô tả nhiệm vụ và trọng tâm bằng tiếng Việt. "
    "Không chấm điểm, không viết nhận xét, không dùng chữ số, không bịa dữ liệu."
)
USER = (
    "Dữ liệu tóm tắt:\n"
    '{"mode":"attempt","attempt_count":1,"score_percentage":62.5,'
    '"weak_concepts":[{"name":"Chuẩn hóa","percentage":37.5},{"name":"Khóa ngoại","percentage":50.0}],'
    '"essay_count":3,"mcq_count":8,"sql_count":1,"trend":"up","details_truncated":false}\n'
    "Trả về JSON với đúng bốn khóa: task_text, focus_text, focus_concepts, format_text. "
    "focus_concepts chỉ chọn từ weak_concepts; format_text là null."
)


def _rss_mb() -> float | None:
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        return None
    return None


def _peak_rss_mb() -> float | None:
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmHWM:"):
                return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        return None
    return None


def _prompt_text(tokenizer) -> tuple[str, int]:
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}]
    if getattr(tokenizer, "chat_template", None):
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        text = f"{SYSTEM}\n\n{USER}\n"
    return text, len(tokenizer(text, add_special_tokens=False)["input_ids"])


def _load(model_name: str, precision: str, *, local_files_only: bool):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dtype = {
        "fp32": torch.float32,
        "bf16": torch.bfloat16,
        "int8": torch.float32,
    }[precision]
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=local_files_only)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, dtype=dtype, local_files_only=local_files_only
    ).eval()
    if precision == "int8":
        model = torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
        model.eval()
    return model, tokenizer, round(time.perf_counter() - started, 3)


def _run_once(model, tokenizer, inputs, max_new_tokens: int):
    import torch

    started = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    elapsed = time.perf_counter() - started
    prompt_tokens = int(inputs["input_ids"].shape[1])
    output_tokens = int(generated.shape[1]) - prompt_tokens
    output = tokenizer.decode(generated[0, prompt_tokens:], skip_special_tokens=True)
    return {
        "seconds": round(elapsed, 4),
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "tokens_per_second": round(output_tokens / elapsed, 2) if elapsed > 0 else 0.0,
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "output_chars": len(output),
    }


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(len(ordered) * q + 0.999999) - 1))
    return round(ordered[index], 3)


def _worker(payload: dict[str, Any]) -> dict[str, Any]:
    os.environ.setdefault("HF_HOME", payload["cache_dir"])
    import torch

    torch.set_num_threads(payload["threads_per_worker"])
    torch.set_num_interop_threads(1)
    model, tokenizer, load_seconds = _load(
        payload["model"], payload["precision"], local_files_only=payload["local_files_only"]
    )
    text, _ = _prompt_text(tokenizer)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
    runs = [_run_once(model, tokenizer, inputs, payload["max_new_tokens"]) for _ in range(payload["runs"])]
    return {
        "pid": os.getpid(),
        "threads": torch.get_num_threads(),
        "load_seconds": load_seconds,
        "rss_after_load_mb": _rss_mb(),
        "peak_rss_mb": _peak_rss_mb(),
        "first_ms": round(runs[0]["seconds"] * 1000, 1),
        "warm_p50_ms": round(_percentile([row["seconds"] * 1000 for row in runs[1:]], 0.5), 1),
        "warm_p95_ms": round(_percentile([row["seconds"] * 1000 for row in runs[1:]], 0.95), 1),
        "prompt_tokens": runs[0]["prompt_tokens"],
        "output_tokens": runs[0]["output_tokens"],
        "runs": runs,
    }


def _host() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "python": platform.python_version(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--precision", choices=["fp32", "bf16", "int8"], default="fp32")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--max-total-rss-mb", type=float, default=3000.0)
    parser.add_argument("--cache-dir", default=os.environ.get("HF_HOME", str(Path.home() / "pb-bench" / "hf")))
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.threads < 1 or args.runs < 1 or args.workers < 1:
        parser.error("threads, runs and workers must be positive")
    os.environ.setdefault("HF_HOME", args.cache_dir)
    if args.workers > args.threads:
        parser.error("workers cannot exceed total threads")
    threads_per_worker = max(1, args.threads // args.workers)
    payload = {
        "model": args.model,
        "precision": args.precision,
        "threads_per_worker": threads_per_worker,
        "runs": args.runs,
        "max_new_tokens": args.max_new_tokens,
        "cache_dir": args.cache_dir,
        "local_files_only": args.local_files_only,
    }
    started = time.perf_counter()
    if args.workers == 1:
        result = _worker(payload)
        wall = round(time.perf_counter() - started, 3)
        result["total_threads"] = result["threads"]
        result["aggregate_peak_rss_mb"] = result["peak_rss_mb"]
        result["wall_seconds"] = wall
        result["memory_limit_exceeded"] = (result["peak_rss_mb"] or 0) > args.max_total_rss_mb
    else:
        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=context) as pool:
            results = list(pool.map(_worker, [payload] * args.workers))
        wall = round(time.perf_counter() - started, 3)
        result = {
            "workers": results,
            "wall_seconds": wall,
            "total_threads": sum(row["threads"] for row in results),
            "aggregate_peak_rss_mb": round(sum(row["peak_rss_mb"] or 0 for row in results), 1),
            "memory_limit_exceeded": sum(row["peak_rss_mb"] or 0 for row in results) > args.max_total_rss_mb,
        }
    report = {
        "benchmark": "framing-cpu-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": _host(),
        "model": args.model,
        "precision": args.precision,
        "threads_requested": args.threads,
        "workers": args.workers,
        "max_total_rss_mb": args.max_total_rss_mb,
        "result": result,
    }
    output = args.output or (DEFAULT_OUTPUT / f"{args.model.replace('/', '__')}-{args.precision}-{args.threads}t-w{args.workers}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "model": args.model,
        "precision": args.precision,
        "threads": result.get("total_threads", result.get("threads")),
        "workers": args.workers,
        "wall_seconds": result.get("wall_seconds"),
        "load_seconds": result.get("load_seconds", (result.get("workers") or [{}])[0].get("load_seconds")),
        "first_ms": result.get("first_ms", (result.get("workers") or [{}])[0].get("first_ms")),
        "warm_p50_ms": result.get("warm_p50_ms", (result.get("workers") or [{}])[0].get("warm_p50_ms")),
        "warm_p95_ms": result.get("warm_p95_ms", (result.get("workers") or [{}])[0].get("warm_p95_ms")),
        "peak_rss_mb": result.get("aggregate_peak_rss_mb"),
        "output_tokens": result.get("output_tokens", (result.get("workers") or [{}])[0].get("output_tokens")),
        "memory_limit_exceeded": result.get("memory_limit_exceeded", False),
        "report": str(output),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
