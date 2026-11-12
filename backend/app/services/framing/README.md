# Framing-only prompt builder (Phase B-0)

This package is a **standalone reference implementation**. It is not imported
by `prompt_builder.py`, `evaluation_pipeline.py` or the evaluation schema. The
running application is unchanged.

## Why framing-only

The current local-model path asks the model to reproduce the whole prompt
(evidence, schema and instructions). Realistic prompts are 18–123 KB, while
the inference entry point truncates input and output to 4,096 tokens. The
model cannot copy what it cannot see or generate. The hybrid design gives all
facts to code and asks the model only for short framing prose.

## Files

| File | Purpose |
| --- | --- |
| `validator.py` | Assembles the reference prompt and validates sections, byte-identical data/schema, framing slots and injection rules. |
| `scanner.py` | PII/secret/URL scanner; findings carry rule + digest, never the matched value. |
| `dataset.py` | Deterministic production-shaped synthetic sessions, split by session, with a dataset hash. |
| `hostile.py` + `data/hostile_cases.json` | 60+ Vietnamese/English hostile learner answers. |
| `gate.py` | Numeric gate; `quality_verified` is computed and cannot be supplied by the caller. |
| `manifest.py` + `data/builder_manifest.schema.json` | Draft artifact manifest and consistency checks. |

## Commands

From the repository root, using the backend environment:

```bash
# Standalone tests; no database, Docker or provider.
cd backend
python -m pytest tests_framing -q

# Generate 300 synthetic sessions into the git-ignored output directory.
python -c "from app.services.framing.dataset import generate, write_dataset; from pathlib import Path; write_dataset(generate(300), Path('../ai/output/framing-dataset'))"

# Evaluate aggregate metrics through the gate.
python -m app.services.framing.gate --metrics ../ai/output/framing-gate/metrics.json
```

## Benchmark results

Environment: Ryzen 5 5600H (6C/12T, 14.9 GB), RTX 3050 Laptop (4 GB, driver
576.88, CUDA 12.9), WSL2 8 GB / 8 CPUs. Benchmarks used 4 threads and hard caps
of 3 GB VRAM and 3 GB host RSS. GPU numbers depend on this machine; a machine
without CUDA must use the template.

### CPU (WSL, no Docker)

| Model | Precision | Output | Warm load | First | Warm p50 / p95 | Tokens/s | Peak RSS | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen2.5-0.5B | FP32 | 99 | 5.48 s | 30.10 s | 30.09 / **40.98 s** | 2.4–3.8 | 3.12 GB | Fail |
| SmolLM2-360M | FP32 | 128 | 3.16 s | 29.06 s | 20.82 / **21.87 s** | 4.4–6.2 | 2.43 GB | Fail |
| Qwen2.5-0.5B | dynamic int8 | — | — | — | — | — | 4.60 GB before generation | Aborted |

First loads including the one-time ~1 GB model download were 162 s (0.5B) and
60.7 s (360M); warm loads are shown above.

### GPU (WSL CUDA, FP16, 3 GB VRAM cap)

| Model | Batch | Output | Warm load | First | Warm p50 / p95 | VRAM reserved / used | Peak RSS | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Qwen2.5-0.5B | 1 | 40 | 3.64 s | 3.64 s | 2.89 / **3.23 s** | 1.02 / 1.47 GB | 2.71 GB | Single fail (7.8% over) |
| Qwen2.5-0.5B | 2 | 40 each | 2.75 s | 3.44 s | 2.74 / **3.47 s** | 1.02 / 1.47 GB | 2.71 GB | Concurrent pass (<5 s) |
| Qwen2.5-0.5B | 1 | 96 | 7.40 s | 7.44 s | 6.20 / **10.04 s** | 1.02 / 1.53 GB | 2.71 GB | Fail |
| SmolLM2-360M | 1 | 40 | 6.93 s | 4.73 s | 3.62 / **4.06 s** | 0.75 / 1.19 GB | 2.17 GB | Fail |

At 40 tokens the Qwen output was only 131 characters (likely truncated); at 96
tokens it was 287 characters but p95 rose to 10.04 s. The 40-token single-request
result is therefore a lower bound, not a complete framing. A 5-run sample measured
3.06 s p95, but the 10-run sample above measured 3.23 s; the single-request gate
is not robustly met.

### Gate comparison

| Gate | Result |
|---|---|
| Single framing p95 ≤ 3 s | **Fail**: 3.23 s at 40 tokens; 10.04 s at 96 |
| Two concurrent p95 ≤ 5 s | **Pass** at 40 tokens: 3.47 s; not run at 96 because single already failed |
| Total builder p95 ≤ 4 s | **Pass only with a persistent model**: 3.25 s single / 3.50 s concurrent. **Fail per-call**: 3.64 s warm load + 3.23 s generation ≈ 6.9 s |
| VRAM < 3 GB | Pass: 1.02 GB reserved; 1.47 GB total including display/context |
| Host RSS < 3 GB | Pass but close: 2.71 GB |
| Quality evidence | **Not run**; `quality_verified` remains false |

The GPU removes the CPU-only 10× gap, but the mandatory **single-request** gate
still misses. The concurrent gate passes only for a truncated 40-token output.
Do not enable the model or start training on this evidence.

### Docker GPU deployment (proposal only)

- The host needs the NVIDIA driver (present), WSL2 GPU support (present), the
  NVIDIA Container Toolkit in the Docker/WSL engine, and a container request
  such as `gpus: all` or a Compose device reservation. The current
  `backend/Dockerfile.ai` is CPU-only; a GPU variant adds a CUDA PyTorch image
  (the isolated venv here is ~5.6 GB installed).
- `mem_limit: 4g` is host RAM, not VRAM. Keep one model process and set
  `torch.cuda.set_per_process_memory_fraction(3000 / total_vram)` inside it.
- The current per-call subprocess is not sufficient: warm load alone is
  2.75–3.64 s, and two concurrent processes duplicate ~1 GB VRAM and ~2.7 GB
  RSS each. A persistent inference process with a queue/batch is required to
  realize the measured single-model numbers.
- If CUDA is unavailable, startup or request-time probe fails, the model is
  absent, or CUDA OOMs, the builder must use the deterministic template and
  record a reason (`cuda_unavailable`, `cuda_oom`, `inference_failed`). The
  default remains `PROMPT_BUILDER_ENABLED=false` with an empty model path.

## Invariants

- Code inserts `canonical(data)` and `canonical(schema)`; the validator hashes
  those blocks byte-for-byte, not just parsed JSON.
- The model never sees learner answers. Its input is an aggregate brief.
- The model selects weak concepts and writes only `task_text` / `focus_text`;
  percentages and concept names are rendered by code.
- `format_text` is optional and allow-listed. Code owns normative formatting.
- Any failure is a template fallback with a stable reason code.
- Dataset targets are marked `status="draft"`; a human must review them before
  training. No real learner data is used.

## Limits

- The 60+ hostile cases prove confinement and validator behavior, not a real
  provider's obedience. That requires the separately approved live run.
- PII detection is pattern-based; arbitrary names need explicit `extra_terms`.
- The gate is only a contract until the benchmark, human review and model
  artifact populate it. `quality_verified=true` must never be set by hand.
