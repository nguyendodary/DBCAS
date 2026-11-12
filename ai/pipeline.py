"""Offline dataset, LoRA training, holdout validation and merged local export."""
import argparse
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.prompt_builder import canonical, template_prompt, validate_prompt

INSTRUCTION = "Chỉ xây dựng prompt đánh giá tiếng Việt gồm BỐI CẢNH, DỮ LIỆU, RUBRIC, SCHEMA JSON, RÀNG BUỘC. Không chấm điểm hay viết nhận xét.\n"


def dataset(output, real=None):
    pack = json.loads((ROOT / "db/benchmark_pack.json").read_text(encoding="utf-8"))
    pairs = []
    for index, question in enumerate(pack["questions"]):
        for variant in range(4):
            data = {"mode": "attempt", "attempt_count": 1, "items": [{
                "attempt_id": index + 1, "question_id": index + 1, "type": question["question_type"],
                "prompt": question["prompt"], "points": question["points"],
                "answer": "" if variant == 0 else question.get("reference_answer", "SELECT * FROM students"),
                "score": None if question["question_type"] == "essay" else (question["points"] if variant > 1 else 0),
                "concepts": question["concept_codes"], "difficulty": question["difficulty_level"],
                "reference_answer": question.get("reference_answer"), "rubric": question.get("rubrics", []),
            }]}
            pairs.append({"input": data, "output": template_prompt(data), "group": question["key"]})
    if real:
        # Explicit export only; never read account rows, keys or a live DB.
        for index, data in enumerate(json.loads(Path(real).read_text(encoding="utf-8"))):
            if any(key in canonical(data).lower() for key in ("email", "password", "api_key", "full_name")):
                raise ValueError("Anonymize the real export before training")
            pairs.append({"input": data, "output": template_prompt(data), "group": f"real-{index}"})
    groups = sorted({p["group"] for p in pairs})
    random.Random(42).shuffle(groups)
    holdout = set(groups[:max(1, len(groups) // 5)])
    output.mkdir(parents=True, exist_ok=True)
    for split in ("train", "test"):
        rows = [p for p in pairs if (p["group"] in holdout) == (split == "test")]
        (output / f"{split}.jsonl").write_text("\n".join(canonical(p) for p in rows) + "\n", encoding="utf-8")
    print(canonical({"pairs": len(pairs), "source": "existing bank + synthetic answers", "real_export": bool(real)}))


def load_model(smoke, model_name):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if not smoke:
        return AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=False), AutoTokenizer.from_pretrained(model_name, trust_remote_code=False)
    from tokenizers import Tokenizer, models, pre_tokenizers, decoders
    from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast
    vocabulary = {"<pad>": 0, "<eos>": 1, "<unk>": 2}
    vocabulary.update({c: i + 3 for i, c in enumerate(pre_tokenizers.ByteLevel.alphabet())})
    tokenizer = Tokenizer(models.BPE(vocab=vocabulary, merges=[], unk_token="<unk>"))
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()
    tokenizer = PreTrainedTokenizerFast(tokenizer_object=tokenizer, pad_token="<pad>", eos_token="<eos>", unk_token="<unk>")
    model = GPT2LMHeadModel(GPT2Config(vocab_size=len(vocabulary), n_positions=512, n_embd=32, n_layer=1, n_head=2))
    return model, tokenizer


def train(output, smoke=False, steps=30, model_name="Qwen/Qwen2.5-0.5B-Instruct"):
    import torch
    from peft import LoraConfig, get_peft_model
    torch.manual_seed(42)
    torch.set_num_threads(2)
    model, tokenizer = load_model(smoke, model_name)
    tokenizer.pad_token = tokenizer.eos_token
    base = output / "base"
    model.save_pretrained(base)
    tokenizer.save_pretrained(base)
    model = get_peft_model(model, LoraConfig(task_type="CAUSAL_LM", r=4, lora_alpha=8,
                          target_modules=["c_attn"] if smoke else ["q_proj", "v_proj"]))
    device = "cuda" if torch.cuda.is_available() and not smoke else "cpu"
    model.to(device).train()
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=2e-4)
    rows = [json.loads(line) for line in (output / "train.jsonl").read_text(encoding="utf-8").splitlines()]
    started = time.monotonic()
    for step in range(2 if smoke else steps):
        row = rows[step % len(rows)]
        prefix = INSTRUCTION + canonical(row["input"]) + "\nPROMPT:\n"
        # Tiny smoke checks optimizer/inference wiring only, not language quality.
        if smoke:
            prefix = "PROMPT:\n"
        tokens = tokenizer(prefix + row["output"] + tokenizer.eos_token, return_tensors="pt", truncation=True, max_length=256 if smoke else 4096)
        labels = tokens["input_ids"].clone()
        prefix_length = len(tokenizer(prefix)["input_ids"])
        labels[:, :prefix_length] = -100
        if (labels != -100).sum() == 0:
            raise ValueError("Training example has no output tokens; reduce input size")
        loss = model(**{k: v.to(device) for k, v in tokens.items()}, labels=labels.to(device)).loss
        if not torch.isfinite(loss):
            raise ValueError("Nonfinite loss")
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
    model.save_pretrained(output / "adapter")
    tokenizer.save_pretrained(output / "adapter")
    (output / "training.json").write_text(canonical({"smoke": smoke, "steps": 2 if smoke else steps,
        "base_model": "tiny-random-gpt2" if smoke else model_name, "device": device,
        "loss": loss.item(), "seconds": round(time.monotonic()-started, 2)}), encoding="utf-8")
    model.merge_and_unload().save_pretrained(output / "export")
    tokenizer.save_pretrained(output / "export")
    print((output / "training.json").read_text())


def infer(data, model_path, max_tokens=4096):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True).eval()
    encoded = tokenizer(INSTRUCTION + canonical(data) + "\nPROMPT:\n", return_tensors="pt", truncation=True, max_length=384 if model.config.model_type == "gpt2" else 4096)
    limit = min(max_tokens, 64) if model.config.model_type == "gpt2" else max_tokens
    with torch.no_grad():
        generated = model.generate(**encoded, max_new_tokens=limit, do_sample=False, pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(generated[0, encoded["input_ids"].shape[1]:], skip_special_tokens=True)


def evaluate_model(output, smoke):
    rows = [json.loads(line) for line in (output / "test.jsonl").read_text(encoding="utf-8").splitlines()]
    valid = 0
    for row in rows[:1 if smoke else 5]:
        try:
            validate_prompt(infer(row["input"], output / "export"), row["input"])
            valid += 1
        except ValueError:
            pass
        validate_prompt(template_prompt(row["input"]), row["input"])
    result = {"evaluated": min(len(rows), 1 if smoke else 5), "valid_model_prompts": valid,
              "template_fallback_valid": True, "quality_verified": False}
    (output / "evaluation.json").write_text(canonical(result), encoding="utf-8")
    print(canonical(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["dataset", "train", "evaluate", "export", "all"])
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "ai/output")
    parser.add_argument("--real")
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    args = parser.parse_args()
    if args.command in ("all", "dataset"): dataset(args.output, args.real)
    if args.command in ("all", "train"): train(args.output, args.smoke, args.steps, args.model)
    if args.command in ("all", "evaluate"): evaluate_model(args.output, args.smoke)
    if args.command == "export":
        if not (args.output / "export/config.json").exists(): raise ValueError("Train before exporting")
        print(args.output / "export")
