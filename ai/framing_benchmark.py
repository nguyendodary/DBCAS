"""CPU/GPU benchmark for the framing-only prompt builder.

This script is intentionally outside the application path.  It loads a local
causal language model, asks it for a short framing JSON object, and records
load, generation, RSS and VRAM metrics.  It never downloads at request time in
production; this benchmark may download the base model into a cache outside the
repository.

CPU example:

    HF_HOME=~/pb-bench/hf python ai/framing_benchmark.py \
      --model Qwen/Qwen2.5-0.5B-Instruct --device cpu --precision fp32 \
      --threads 4 --runs 5 --max-new-tokens 160

GPU example (one model, two batched requests):

    HF_HOME=~/pb-bench/hf python ai/framing_benchmark.py \
      --model Qwen/Qwen2.5-0.5B-Instruct --device cuda --precision fp16 \
      --threads 4 --runs 5 --max-new-tokens 40 --batch-size 2 \
      --max-vram-mb 3000

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
import subprocess
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


def _nvidia_smi_used_mb() -> int | None:
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL, timeout=10,
        ).strip().splitlines()
        return int(output[0].strip()) if output else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _prompt_text(tokenizer) -> str:
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}]
    if getattr(tokenizer, "chat_template", None):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return f"{SYSTEM}\n\n{USER}\n"


def _make_inputs(tokenizer, text: str, batch_size: int, device):
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
    return {key: value.repeat(batch_size, 1).to(device) for key, value in inputs.items()}


def _load(
    model_name: str,
    precision: str,
    device,
    *,
    local_files_only: bool,
    max_vram_mb: float | None,
):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    vram: dict[str, Any] = {}
    if device.type == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
        torch.cuda.init()
        free_bytes, total_bytes = torch.cuda.mem_get_info()
        total_mb = total_bytes / (1024 * 1024)
        vram = {
            "name": torch.cuda.get_device_name(0),
            "total_mb": round(total_mb, 1),
            "free_before_mb": round(free_bytes / (1024 * 1024), 1),
            "cuda": torch.version.cuda,
        }
        if max_vram_mb:
            fraction = min(1.0, max_vram_mb / total_mb)
            torch.cuda.set_per_process_memory_fraction(fraction, 0)
            vram["cap_mb"] = round(max_vram_mb, 1)
            vram["cap_fraction"] = round(fraction, 3)
        torch.cuda.reset_peak_memory_stats()

    dtype = {
        "fp32": torch.float32,
        "fp16": torch.float16,
        "bf16": torch.bfloat16,
        "int8": torch.float32,
    }[precision]
    if precision == "int8" and device.type == "cuda":
        raise ValueError("dynamic int8 is CPU-only; use fp16 on CUDA")
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=local_files_only)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, dtype=dtype, local_files_only=local_files_only
    ).eval()
    if precision == "int8":
        model = torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
        model.eval()
    model.to(device)
    if device.type == "cuda":
        torch.cuda.synchronize()
        vram["attn_implementation"] = getattr(model.config, "_attn_implementation", None)
    return model, tokenizer, round(time.perf_counter() - started, 3), vram


def _run_once(model, tokenizer, inputs, max_new_tokens: int, batch_size: int):
    import torch

    if inputs["input_ids"].is_cuda:
        torch.cuda.synchronize()
    started = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    if inputs["input_ids"].is_cuda:
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - started
    prompt_tokens = int(inputs["input_ids"].shape[1])
    output_tokens = int(generated.shape[1]) - prompt_tokens
    texts = [
        tokenizer.decode(generated[index, prompt_tokens:], skip_special_tokens=True)
        for index in range(int(generated.shape[0]))
    ]
    return {
        "seconds": round(elapsed, 4),
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "total_output_tokens": output_tokens * batch_size,
        "tokens_per_second": round(output_tokens * batch_size / elapsed, 2) if elapsed > 0 else 0.0,
        "output_sha256": hashlib.sha256("\n".join(texts).encode("utf-8")).hexdigest(),
        "output_chars": sum(len(text) for text in texts),
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
    device = torch.device(payload["device"])
    vram_before = {}
    gpu_used_before = None
    if device.type == "cuda":
        torch.cuda.init()
        gpu_used_before = _nvidia_smi_used_mb()
        free_bytes, total_bytes = torch.cuda.mem_get_info()
        vram_before = {
            "total_mb": round(total_bytes / (1024 * 1024), 1),
            "free_before_mb": round(free_bytes / (1024 * 1024), 1),
            "gpu_used_before_mb": gpu_used_before,
        }
    try:
        model, tokenizer, load_seconds, vram = _load(
            payload["model"], payload["precision"], device,
            local_files_only=payload["local_files_only"],
            max_vram_mb=payload["max_vram_mb"],
        )
    except torch.cuda.OutOfMemoryError:
        return {"status": "cuda_oom", "vram_before": vram_before}
    text = _prompt_text(tokenizer)
    inputs = _make_inputs(tokenizer, text, payload["batch_size"], device)
    try:
        runs = [
            _run_once(model, tokenizer, inputs, payload["max_new_tokens"], payload["batch_size"])
            for _ in range(payload["runs"])
        ]
    except torch.cuda.OutOfMemoryError:
        return {"status": "cuda_oom_generation", "vram_before": vram_before}
    vram_after = dict(vram_before)
    vram_after.update(vram)
    if device.type == "cuda":
        allocated = torch.cuda.max_memory_allocated() / (1024 * 1024)
        reserved = torch.cuda.max_memory_reserved() / (1024 * 1024)
        free_after, total_after = torch.cuda.mem_get_info()
        vram_after.update({
            "peak_allocated_mb": round(allocated, 1),
            "peak_reserved_mb": round(reserved, 1),
            "free_after_mb": round(free_after / (1024 * 1024), 1),
            "total_after_mb": round(total_after / (1024 * 1024), 1),
            "gpu_used_after_mb": _nvidia_smi_used_mb(),
            "limit_exceeded": bool(payload["max_vram_mb"] and reserved > payload["max_vram_mb"]),
        })
    return {
        "status": "ok",
        "pid": os.getpid(),
        "device": str(device),
        "threads": torch.get_num_threads(),
        "load_seconds": load_seconds,
        "rss_after_load_mb": _rss_mb(),
        "peak_rss_mb": _peak_rss_mb(),
        "vram": vram_after,
        "first_ms": round(runs[0]["seconds"] * 1000, 1),
        "warm_p50_ms": round(_percentile([row["seconds"] * 1000 for row in runs[1:]], 0.5), 1),
        "warm_p95_ms": round(_percentile([row["seconds"] * 1000 for row in runs[1:]], 0.95), 1),
        "prompt_tokens": runs[0]["prompt_tokens"],
        "output_tokens": runs[0]["output_tokens"],
        "tokens_per_second": runs[0]["tokens_per_second"],
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
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--precision", choices=["fp32", "fp16", "bf16", "int8"], default="fp32")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--max-new-tokens", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--max-total-rss-mb", type=float, default=3000.0)
    parser.add_argument("--max-vram-mb", type=float, default=3000.0)
    parser.add_argument("--cache-dir", default=os.environ.get("HF_HOME", str(Path.home() / "pb-bench" / "hf")))
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.threads < 1 or args.runs < 1 or args.workers < 1 or args.batch_size < 1:
        parser.error("threads, runs, workers and batch-size must be positive")
    if args.device == "cuda" and args.workers > 1:
        parser.error("CUDA concurrency uses one process and --batch-size; multiple workers duplicate VRAM")
    if args.device == "cuda" and args.precision == "int8":
        parser.error("dynamic int8 is CPU-only; use --precision fp16 on CUDA")
    if args.device == "cpu" and args.precision == "fp16":
        parser.error("fp16 requires --device cuda")
    if args.workers > args.threads:
        parser.error("workers cannot exceed total threads")
    os.environ.setdefault("HF_HOME", args.cache_dir)
    threads_per_worker = max(1, args.threads // args.workers)
    payload = {
        "model": args.model,
        "device": args.device,
        "precision": args.precision,
        "threads_per_worker": threads_per_worker,
        "runs": args.runs,
        "max_new_tokens": args.max_new_tokens,
        "batch_size": args.batch_size,
        "cache_dir": args.cache_dir,
        "local_files_only": args.local_files_only,
        "max_vram_mb": args.max_vram_mb,
    }
    started = time.perf_counter()
    if args.workers == 1:
        result = _worker(payload)
        wall = round(time.perf_counter() - started, 3)
        result["wall_seconds"] = wall
        result["aggregate_peak_rss_mb"] = result.get("peak_rss_mb")
        result["memory_limit_exceeded"] = (result.get("peak_rss_mb") or 0) > args.max_total_rss_mb
        result["total_threads"] = result.get("threads")
    else:
        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=context) as pool:
            results = list(pool.map(_worker, [payload] * args.workers))
        wall = round(time.perf_counter() - started, 3)
        result = {
            "workers": results,
            "wall_seconds": wall,
            "total_threads": sum(row.get("threads") or 0 for row in results),
            "aggregate_peak_rss_mb": round(sum(row.get("peak_rss_mb") or 0 for row in results), 1),
            "memory_limit_exceeded": sum(row.get("peak_rss_mb") or 0 for row in results) > args.max_total_rss_mb,
        }
    report = {
        "benchmark": "framing-cpu-gpu-v2",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": _host(),
        "model": args.model,
        "device": args.device,
        "precision": args.precision,
        "batch_size": args.batch_size,
        "threads_requested": args.threads,
        "workers": args.workers,
        "max_total_rss_mb": args.max_total_rss_mb,
        "max_vram_mb": args.max_vram_mb,
        "result": result,
    }
    output = args.output or (
        DEFAULT_OUTPUT
        / f"{args.model.replace('/', '__')}-{args.device}-{args.precision}-{args.threads}t-b{args.batch_size}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    first = result if args.workers == 1 else (result.get("workers") or [{}])[0]
    summary = {
        "model": args.model,
        "device": args.device,
        "precision": args.precision,
        "batch_size": args.batch_size,
        "threads": result.get("total_threads"),
        "wall_seconds": result.get("wall_seconds"),
        "load_seconds": first.get("load_seconds"),
        "first_ms": first.get("first_ms"),
        "warm_p50_ms": first.get("warm_p50_ms"),
        "warm_p95_ms": first.get("warm_p95_ms"),
        "tokens_per_second": first.get("tokens_per_second"),
        "peak_rss_mb": result.get("aggregate_peak_rss_mb"),
        "vram": first.get("vram"),
        "status": first.get("status"),
        "memory_limit_exceeded": result.get("memory_limit_exceeded"),
        "report": str(output),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if first.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
