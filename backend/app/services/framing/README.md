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
