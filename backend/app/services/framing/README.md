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
  current default is an empty `PROMPT_BUILDER_MODEL_PATH`; the proposed enable
  flag is `PROMPT_BUILDER_ENABLED=false` (not wired into the app).

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

## AI local: đã thực hiện và hạn chế

> Trạng thái: **đã thực hiện ở mức research/reference, có hạn chế**. Mô hình
> **không** được triển khai trong ứng dụng đang chạy, **không** huấn luyện và
> **chưa** được xác nhận chất lượng. Đường chạy production vẫn là template xác
> định.

### Mục tiêu và vai trò của AI #1

AI #1 chỉ có một việc: nhận toàn bộ dữ liệu của một bài kiểm tra đã hoàn thành
và soạn **một** prompt tiếng Việt có cấu trúc cho AI #2. AI #1 không chấm điểm,
không viết lại câu trả lời của người học, không tạo nhận xét và không trả kết
quả đánh giá. Mọi dữ kiện (điểm, ID, tên khái niệm, phần trăm, câu trả lời,
rubric) phải do code chèn nguyên văn; AI #2 mới là nơi đọc prompt và trả JSON
đánh giá.

### Thiết kế hybrid

- Code sở hữu toàn bộ dữ kiện và phần quy chuẩn: `canonical(data)`,
  `canonical(schema)`, rubric, ràng buộc định dạng và phần trăm khái niệm.
- Mô hình chỉ viết phần framing ngắn: `task_text`, `focus_text`, lựa chọn
  `focus_concepts` và tùy chọn `format_text` đã được allow-list. Mô hình **không
  nhìn thấy câu trả lời của người học**; đầu vào là một brief tổng hợp.
- `validate_prompt` kiểm tra đủ section, thứ tự, hash byte-identical cho
  `DỮ LIỆU`/`SCHEMA JSON`, độ dài, PII/secret/URL, số/ID, grade phrase, copy câu
  trả lời và concept ngoài brief. Mọi lỗi quay về template với reason code.
- `builder_fallback`/reason code được thiết kế để ghi nhận; template là mặc
  định an toàn.

### Đã thực hiện

- `validator.py`: validator/assembly tham chiếu, hỗ trợ 5 hoặc 6 section (kể cả
  `## KHÁI NIỆM` sau này), byte-hash dữ liệu/schema, kiểm tra framing slot.
- `scanner.py`: quét email, số điện thoại, labelled ID, URL, JWT, API key,
  GitHub/AWS token, private key, `client_secret`; finding chỉ trả rule + digest,
  không trả giá trị khớp.
- `hostile.py` + `data/hostile_cases.json`: 65 ca hostile tiếng Việt/Anh, 20
  nhóm; tất cả bị giữ trong block dữ liệu, copy sang framing bị từ chối.
- `dataset.py`: generator session tổng hợp đúng shape production; 300 session
  (210 train / 45 validation / 45 test), chia theo session, dataset hash
  `74fd5420…a596b`, fixture hash `75f72745…b0bf2`, 0 PII, target `status="draft"`.
- `manifest.py` + `data/builder_manifest.schema.json`: manifest bắt buộc
  `quality_verified`; gate report phải khớp metrics và `report_hash`, không thể
  tự đặt `quality_verified=true`.
- `gate.py`: threshold số cho section, fidelity, PII/secret, injection, length,
  latency, fallback và value; `quality_verified` chỉ do gate tính.
- `ai/framing_benchmark.py`: harness CPU/GPU, batch, VRAM/RSS, cold/warm load.
- `backend/tests_framing`: 54 test standalone; không cần DB/Docker/provider.
- Module **không** được import bởi `prompt_builder.py` hay
  `evaluation_pipeline.py`; đây là reference module, không phải đường chạy.

### Kết quả đo

Phần cứng: Ryzen 5 5600H (6C/12T, 14.9 GB RAM), RTX 3050 Laptop 4 GB (driver
576.88, CUDA 12.9), WSL2 8 GB / 8 CPU. Đo với 4 thread, giới hạn 3 GB VRAM và
3 GB RSS. Kết quả GPU phụ thuộc máy này; máy không có CUDA phải dùng template.

- **CPU, Qwen2.5-0.5B FP32:** warm load 5.48 s; first 30.10 s; warm p50
  **30.09 s**, p95 **40.98 s**; 2.4–3.8 token/s; peak RSS 3.12 GB. Không đạt.
- **CPU, SmolLM2-360M FP32:** warm load 3.16 s; p50 **20.82 s**, p95
  **21.87 s**; peak RSS 2.43 GB. Không đạt.
- **CPU, dynamic int8:** RSS tăng **4.60 GB** trong lúc nạp/quantize; đã dừng,
  không khả thi trong giới hạn.
- **GPU, Qwen2.5-0.5B FP16, batch 1, 40 token:** warm load 3.64 s; first
  3.64 s; warm p50 **2.89 s**, p95 **3.23 s**; VRAM 1.02 GB reserved / 1.47 GB
  total; RSS 2.71 GB. **Không đạt** ngưỡng single p95 ≤ 3 s (7.8% over; mẫu
  5 lần từng đo 3.06 s, mẫu 10 lần là 3.23 s).
- **GPU, batch 2, 40 token mỗi request:** warm load 2.75 s; p50 **2.74 s**, p95
  **3.47 s**; VRAM 1.02/1.47 GB; RSS 2.71 GB. Đạt ngưỡng concurrent p95 ≤ 5 s.
- **GPU, batch 1, 96 token:** warm load 7.40 s; p50 **6.20 s**, p95
  **10.04 s**; VRAM 1.02/1.53 GB. Không đạt; đây là mức gần với framing 2–3 slot
  hơn, vì 40 token chỉ sinh 131 ký tự (có thể bị cắt).
- **GPU, SmolLM2-360M FP16, 40 token:** p95 **4.06 s**; VRAM 0.75/1.19 GB; RSS
  2.17 GB. Không đạt.

So với CPU, GPU rút ngắn khoảng cách khoảng 10 lần nhưng **vẫn không đạt gate
single-request**. Batch 2 đạt gate concurrent nhưng chỉ với output 40 token có
thể đã bị cắt. Chưa có đánh giá chất lượng bằng blind review; `quality_verified`
vẫn là `false`.

### Hạn chế

- **Tài nguyên:** CPU ~30–41 s/prompt (0.5B); GPU FP16 ~3.2 s ở 40 token và ~10 s
  ở 96 token, trong khi mục tiêu là ≤ 3 s single. VRAM ~1.0–1.5 GB, RSS ~2.7 GB;
  hai process đồng thời sẽ nhân đôi tài nguyên.
- **Load time:** warm load 2.75–3.64 s (40 token) và 7.40 s (96 token); per-call
  subprocess cộng load vào latency và vượt tổng builder ≤ 4 s. Cần persistent
  inference process nếu muốn dùng mô hình.
- **Triển khai:** cần GPU passthrough qua NVIDIA Container Toolkit và image CUDA
  (image lớn); hiện `backend/Dockerfile.ai` là CPU-only. Máy không có GPU/CUDA
  phải fallback template.
- **Chất lượng:** chưa đánh giá bằng blind review; 40 token có thể chưa đủ cho
  framing 2–3 slot; 96 token làm p95 tăng mạnh. Không có bằng chứng mô hình tốt
  hơn template adaptive.
- **Phạm vi:** kết quả chỉ đúng cho cấu hình máy này; không đại diện cho CI, máy
  không GPU hoặc phần cứng khác.

### Quyết định

Production dùng **deterministic adaptive template + strict byte-hash
validator**. Mô hình local **mặc định OFF**: hiện tại
`PROMPT_BUILDER_MODEL_PATH` rỗng; flag đề xuất `PROMPT_BUILDER_ENABLED=false`
(chưa nối vào code); `quality_verified=false`. Không huấn luyện, không bật mô
hình, không thay `prompt_builder.py`/`evaluation_pipeline.py`/evaluation schema.
Module này được giữ trong repo như tài liệu nghiên cứu/reference và có thể được
mở lại sau.

### Hướng tiếp theo

- GGUF/llama.cpp hoặc quantization phù hợp CPU/GPU nhỏ, chỉ sau khi đo lại.
- Một inference service riêng, persistent, có queue/batch và fallback rõ ràng.
- Phần cứng mạnh hơn hoặc GPU passthrough ổn định trong Docker.
- Framing target ngắn hơn (một slot ngắn) và blind review chất lượng trước khi
  xét `quality_verified=true`.
- Mọi hướng tiếp theo cần approval riêng; không tự động bật mô hình.
