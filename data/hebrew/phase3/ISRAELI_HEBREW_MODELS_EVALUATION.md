# Israeli Hebrew Models Evaluation — Optional Contextual Evaluator Agents

## 1. Scope and Constraints

This evaluation examines two open-weight Hebrew-language models as **optional advisory agents** for the shared Hebrew linguistic engine.

Intended advisory tasks:
- sentence naturalness
- morphological disambiguation
- register classification
- semantic plausibility
- contextual error diagnosis
- comparison of accepted variants

Hard constraints:
- The deterministic linguistic engine is **not** replaced.
- LLM output is **advisory only** and may not create or modify automatic gold records.
- A record may be promoted only through the existing evidence and approval pipeline.
- No 9.5/10 reliability claim is made for the LLM itself.

## 2. Model Overview

| Model | Family | License | Sizes | Architecture | Native Context |
|-------|--------|---------|-------|--------------|----------------|
| **DictaLM 3.0** | 24B / 12B / 1.7B | Apache-2.0 | Base, Instruct, Thinking, FP8, W4A16, GGUF, MLX | Mistral-Small / Nemotron / Qwen3 derivatives | 65,536 tokens |
| **HEBATRON** | 31.6B total (~3B active) | Apache-2.0 | Base, base_long, FP8, GGUF, MLX | Hybrid Mamba2 SSM + Sparse MoE (Nemotron-3-Nano-30B) | 8,096 / 65,536 tokens |

Both models are released by Israeli research groups and are explicitly optimised for Hebrew.

## 3. DictaLM 3.0

### 3.1 Available weights

Hugging Face repos (verified 2026-07-23):
- `dicta-il/DictaLM-3.0-24B-Base`, `-24B-Thinking`, `-24B-Instruct`
- `dicta-il/DictaLM-3.0-Nemotron-12B-Base`, `-Nemotron-12B-Instruct`
- `dicta-il/DictaLM-3.0-1.7B-Base`, `-1.7B-Instruct`, `-1.7B-Thinking`
- Quantized/converted variants: FP8, W4A16, GGUF (Q4_K_M, Q5_K_M, Q8_0, BF16), MLX fp16/8-bit.

### 3.2 License

Apache-2.0 (displayed on every Hugging Face model card and in the technical report). Commercial use and redistribution of the model weights are allowed with standard Apache-2.0 attribution. Generated advisory text from a locally run model is our own derivative output and is not encumbered by the model license.

### 3.3 Hardware requirements

| Variant | Precision | Approx. file size | VRAM/RAM need (inference) |
|---------|-----------|-------------------|---------------------------|
| 1.7B Instruct | BF16 | 3.4 GB | 3–4 GB |
| 1.7B Instruct | FP8 | <2 GB | <4 GB |
| 1.7B Instruct | Q4_K_M GGUF | 1.11 GB | ~2–3 GB |
| 1.7B Instruct | MLX fp16 | 3.44 GB | ~3–4 GB |
| 1.7B Instruct | MLX 8-bit | 1.83 GB | ~2–3 GB |
| 24B Base | BF16 | ~48 GB | ~48–64 GB |
| 24B Thinking | FP8 | ~24 GB | L40S 48 GB recommended |
| 24B Thinking | W4A16 | ~13–15 GB | 24 GB GPU |
| 24B Thinking | Q4_K_M GGUF | ~13.5 GB | ~16–20 GB RAM |
| 24B Thinking | MLX 8-bit | 25 GB | 32–48 GB unified memory |

### 3.4 Quantized versions

Official quantized releases exist for FP8, W4A16, GGUF and MLX. Community GGUF/MLX conversions are also available. The 1.7B Q4_K_M GGUF is the most portable for CPU/edge inference.

### 3.5 Apple Silicon compatibility

MLX conversions exist for 1.7B, 12B and 24B variants (`ssdataanalysis/DictaLM-3.0-*-mlx-*`). 1.7B runs comfortably on any Apple Silicon Mac with 8 GB unified memory. 24B 8-bit (25 GB) realistically needs a 32–48 GB Mac and will be bandwidth-constrained. `mlx-lm` supports Qwen3, Mistral and Nemotron architectures used by DictaLM 3.0.

### 3.6 Raspberry Pi feasibility

Only the 1.7B Q4_K_M GGUF (1.11 GB) is feasible. It fits in the RAM of a Raspberry Pi 4/5 8 GB. Expected decode speed on a Pi 5 is roughly 5–10 tokens/second; on Pi 4 4 GB it would be marginal due to OS overhead. The 12B and 24B variants are not feasible on Pi-class hardware.

### 3.7 Python inference options

- `transformers` pipeline (use `trust_remote_code=True` for Nemotron/Mistral/Qwen3).
- `vllm serve` (recommended by Dicta for production; supports tool calling via Hermes parser).
- `llama.cpp` / `llama-cpp-python` for GGUF.
- `mlx-lm` for Apple Silicon (`load`, `generate`, `mlx_lm.server`).
- `ollama`, LM Studio, Jan for end-user apps.

### 3.8 Expected latency

Approximate decode tokens/second (community/authoritative benchmarks):

| Variant / backend | Hardware | Decode tok/s |
|-------------------|----------|--------------|
| 1.7B MLX | Apple M4 Max | ~150–290 |
| 1.7B GGUF Q4_K_M | Raspberry Pi 5 8 GB | ~5–10 |
| 1.7B GGUF Q4_K_M | Desktop CPU (8 threads) | ~20–50 |
| 24B MLX 8-bit | Apple M4 Max 64 GB | ~5–15 |
| 24B GGUF Q4_K_M | RTX 4090 / 24 GB | ~10–30 |
| 24B FP8 | L40S 48 GB | ~20–40 |

Prompt-processing (prefill) is much faster and memory-bandwidth-bound on Apple Silicon.

### 3.9 Context length

Native context is 65,536 tokens. The MLX conversion pages list a "Large Context Window" of 40,960 tokens for the 1.7B variant. For evaluator tasks (single sentences or short paragraphs), even 4,096 tokens is plenty.

### 3.10 Hebrew benchmark results

Hebrew LLM Leaderboard (base few-shot):

| Model | Avg. | vs. Base |
|-------|------|----------|
| DictaLM-3.0-24B | 72.5 | +6.5 vs. Mistral-Small-3.1-24B |
| DictaLM-3.0-Nemotron-12B | 66.5 | +12.8 vs. Nemotron-Nano-12B-v2 |
| DictaLM-3.0-1.7B | 51.5 | +8.2 vs. Qwen3-1.7B-Base |

New Hebrew chat benchmark (Table 8 from the technical report):

| Task | 24B-Thinking | 12B-Instruct | 1.7B-Instruct |
|------|--------------|--------------|---------------|
| Summarization | 78.06 | 33.27 | 9.72 |
| Translation | 56.86 | 13.50 | 2.16 |
| Winogrande | 30.09 | 73.74 | 30.21 |
| Israeli Trivia | 60.13 | 45.18 | 58.20 |
| Nikud (diacritization) | 86.86 | 76.12 | 52.76 |

AlephBench (HebArabNlpProject) for `dicta-il/DictaLM-3.0-24B-Thinking`:

| AlephBench | MMLU | ARC | HellaSwag | GSM8K | COPA | Hebrew-QA | HebNLI | Winograd | Sentiment | Trivia | Translation |
|------------|------|-----|-----------|-------|------|-----------|--------|----------|-----------|--------|-------------|
| 85.2 | 79.0 | 92.5 | 69.8 | 96.3 | 95.1 | 97.8 | 82.0 | 77.2 | 75.2 | 86.4 | 86.1 |

English capability retention is reported as >98%.

## 4. HEBATRON

### 4.1 Available weights

Hugging Face repos (verified 2026-07-23):
- `HebArabNlpProject/Hebatron` (chat/instruct, 64k context)
- `HebArabNlpProject/Hebatron_base` (8k context)
- `HebArabNlpProject/Hebatron_base_long` (64k context)
- Community GGUF (`itayl/Hebatron-Q4_K_M-GGUF`, `mradermacher/Hebatron-GGUF`, `mradermacher/Hebatron-i1-GGUF`)
- Community MLX (`ssdataanalysis/Hebatron-mlx-fp16`, `ssdataanalysis/Hebatron-mlx-8Bit`)

### 4.2 License

Apache-2.0 (displayed on the Hugging Face model card). Same commercial-use caveats as DictaLM.

### 4.3 Hardware requirements

| Variant | Approx. file size | VRAM/RAM need |
|---------|-------------------|---------------|
| BF16 / FP8 full | ~63 GB | NVIDIA Blackwell B300 / H200 recommended |
| Q4_K_M GGUF | 24.5 GB | ~28–32 GB RAM |
| Q8_0 GGUF | 33.7 GB | ~40 GB RAM |
| MLX fp16 | 63.2 GB | Mac with 64–96 GB unified memory |
| MLX 8-bit | 33.6 GB | Mac with 40–48 GB unified memory |

### 4.4 Quantized versions

GGUF exists from Q2_K through Q8_0 and imatrix variants. MLX 8-bit and fp16 conversions exist. The official FP8 release targets Hopper/Blackwell data-center GPUs.

### 4.5 Apple Silicon compatibility

`ssdataanalysis/Hebatron-mlx-8Bit` is explicitly converted for MLX. However, HEBATRON uses a hybrid Mamba2 SSM + Sparse MoE architecture derived from Nemotron-3-Nano-30B-A3B. `llama.cpp` added Mamba-2 support and MoE support, and the MLX conversion loaded successfully, but large MoE models on Apple Silicon still have edge cases (e.g. V-cache quantization bugs on some MoE models). A 33.6 GB model requires a 48–64 GB Apple Silicon Mac and will be slow. HEBATRON is **not** a low-end Apple-Silicon target.

### 4.6 Raspberry Pi feasibility

Not feasible as a single-device deployment. The smallest usable GGUF is ~18–24 GB, exceeding the 16 GB maximum RAM of a Raspberry Pi 5. Clustering (e.g. NanoCamelid) is theoretically possible but outside the scope of this evaluation.

### 4.7 Python inference options

- `vllm serve` (recommended by the authors).
- `transformers` with `trust_remote_code=True`.
- `llama.cpp` GGUF via `llama-cli` / `llama-server` / `llama-cpp-python`.
- `mlx-lm` for the MLX conversions on Apple Silicon.

### 4.8 Expected latency

On recommended NVIDIA H200/B300 hardware HEBATRON is reported to deliver ~9× higher inference throughput than comparable dense 27B models because it activates only ~3B parameters per token. On consumer Apple Silicon (MLX 8-bit, 33.6 GB) expect roughly 2–8 tokens/second; on CPU-only 24.5 GB GGUF expect 1–4 tokens/second.

### 4.9 Context length

65,536 tokens for `Hebatron` and `Hebatron_base_long`; 8,096 for `Hebatron_base`.

### 4.10 Hebrew benchmark results

Author-reported Hebrew benchmarks:

| Metric | Score |
|--------|-------|
| Hebrew Average Reasoning | 73.8% |
| SNLI (Hebrew semantic reasoning) | 91.2% |
| Israeli Trivia | 72.1% |
| GSM8K (Hebrew) | 83.3% |
| English Reasoning Average | 86.0% |

AlephBench row for `HebArabNlpProject/Hebatron`:

| AlephBench | MMLU | ARC | HellaSwag | GSM8K | COPA | Hebrew-QA | HebNLI | Winograd | Sentiment | Trivia | Translation |
|------------|------|-----|-----------|-------|------|-----------|--------|----------|-----------|--------|-------------|
| 77.1 | 67.3 | 85.2 | 57.1 | 87.3 | 76.1 | 95.1 | 65.2 | 69.1 | 69.3 | 92.4 | 84.1 |

HEBATRON outperforms `DictaLM-3.0-24B-Thinking` on the author Hebrew-reasoning average (73.8% vs. 68.9%) and on Israeli Trivia, while activating fewer parameters per token.

## 5. Reproducible Prompt Format

Both models are chat-template models. The recommended reproducible pipeline is:

1. Build a message list with a system role that states the advisory-only rule.
2. Apply the model's Hugging Face chat template (`tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)`).
3. Set `temperature=0.0` and a fixed `seed` when the backend supports it.
4. Request a JSON object matching a documented schema.

Example prompt structure (used by `hebrew/phase3/evaluator_agent.py`):

```json
[
  {
    "role": "system",
    "content": "אתה עוזר לשוני לעברית מודרנית. התוצר שלך הוא ייעוצי בלבד ואינו משנה רשומות זהב אוטומטיות. אם אינך בטוח, הגדר abstain=true."
  },
  {
    "role": "user",
    "content": "Task: sentence_naturalness\nText: <hebrew sentence>\nContext: {...}\n\nReturn valid JSON matching this schema: {...}"
  }
]
```

For `llama.cpp` add `--jinja` so the chat template is applied automatically. For `vllm` use the OpenAI-compatible chat-completions endpoint. For `mlx-lm` apply the chat template in Python before calling `generate`.

## 6. Structured JSON Output Reliability

Neither model is fine-tuned specifically for JSON-only generation. Raw output must be treated as unreliable and post-processed.

Best practices:
- Use `temperature=0.0` and, if supported, `seed` for deterministic sampling.
- Use constrained decoding when available:
  - `vllm` supports guided decoding (Outlines / xgrammar / lm-format-enforcer).
  - `llama.cpp` supports grammar-based JSON output.
  - `mlx-lm` currently has no built-in grammar; parse and validate.
- Extract the first JSON object from the response (handle ```json fences).
- Validate with the schema; on failure, set `abstention_status=abstain`.
- Never treat an unparsed or malformed response as evidence.

The `EvaluatorResult` object in `hebrew/phase3/evaluator_agent.py` stores both `parsed_json` and `raw_response` so every call is auditable.

## 7. Proposed Interface

A reference implementation is provided in `hebrew/phase3/evaluator_agent.py`.

Key components:
- `EvaluatorResult` — structured output with confidence, alternatives, explanation, model identity, prompt version, deterministic-engine agreement, and abstention flag.
- `HebrewEvaluatorAgent` — abstract base class exposing advisory methods:
  - `evaluate_sentence_naturalness`
  - `disambiguate_morphology`
  - `classify_register`
  - `assess_semantic_plausibility`
  - `diagnose_contextual_error`
  - `compare_variants`
- `DictaLMEvaluator` — adapter for DictaLM 3.0 with auto backend selection (`mlx`, `llama_cpp`, `vllm`, `transformers`).
- `HebatronEvaluator` — adapter for HEBATRON using the same contract.
- `MockEvaluator` — deterministic mock for unit tests and CI.

Every concrete adapter:
- records the exact prompt in `prompt_used`;
- returns `advisory_only=True`;
- compares the parsed result with the deterministic engine's result;
- defaults to `abstention_status=abstain` when confidence < 0.6 or the response cannot be parsed.

## 8. Integration Rules

1. **No gold creation or modification.** LLM advice is stored as `source_evidence` with `source_id` set to the model identifier and `source_eligibility` set to `private_research_only` or `reference_only` until a separate validation step confirms it.
2. **Promotion through existing pipeline.** A record can become `verified_automatic_gold` only by satisfying the existing evidence consensus, confidence calibration and approval rules; an LLM result is one optional input, not a deciding vote.
3. **Deterministic engine veto.** If the evaluator disagrees with the deterministic engine, the deterministic result prevails unless new independent evidence overturns it.
4. **Version pinning.** Every result includes `model_identity`, `model_version` and `prompt_version` for reproducibility.
5. **Abstention by default.** Low-confidence, malformed or conflicting evaluator output must be treated as abstention.

## 9. Recommendation

**Do not integrate either model as a required component before continuing the deterministic Phase 3 work.** The core engine, orthography, phonology, gold expansion, benchmark and metrics must remain deterministic and auditable. LLM-based evaluators are optional advisers that can be added after the deterministic baseline is in place.

If an optional evaluator is desired during Phase 3, the recommended choice is:

- **DictaLM 3.0 1.7B Instruct** (or `DictaLM-3.0-1.7B-Instruct-mlx-fp16` / Q4_K_M GGUF)
  - Apache-2.0, small enough for Apple Silicon, desktops and Raspberry Pi.
  - Easy to run with `mlx-lm`, `llama.cpp` or `transformers`.
  - Lower per-task accuracy than 24B/HEBATRON but sufficient for advisory checks.

**HEBATRON** should be deferred:
- Requires high-end GPU or 48–64 GB Apple Silicon.
- Mamba2 + MoE stack is more complex and less battle-tested on consumer hardware.
- Best reserved for later phases when a high-quality, high-latency contextual adviser is justified.

Neither model has been benchmarked on the specific internal morphology, spelling, stress and shva tasks of this engine. Before any LLM advice is used to influence approvals, run a measured comparison against the deterministic engine on a held-out validation partition and report `deterministic_engine_agreement` and `abstention_rate`.

## 10. Next Steps

1. Continue Phase 3 deterministic engine implementation.
2. Keep `hebrew/phase3/evaluator_agent.py` as a stable adapter interface.
3. After the deterministic benchmark is frozen, add an optional `DictaLMEvaluator` pipeline and measure:
   - JSON parse success rate
   - agreement with deterministic engine
   - human/linguist acceptance rate on a small sample
   - latency per call
4. Only if the optional evaluator demonstrates measurable value with no regression to gold-approval gates, allow it to contribute evidence with `trust_tier` lower than `manual_override` and `production_eligibility` no higher than `private_research_only`.
