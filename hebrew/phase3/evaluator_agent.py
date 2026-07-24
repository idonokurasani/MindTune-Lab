"""Optional advisory Hebrew-language evaluator agents.

These adapters wrap local Hebrew LLMs (DictaLM 3.0 and HEBATRON) and use them
only as contextual advisers.  They never create, modify, or promote automatic
gold records.  Any evaluator result must be merged into the deterministic engine's
evidence pipeline by the existing approval layer.
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class EvaluatorResult:
    """Structured output of an LLM-based Hebrew evaluator."""

    proposed_analysis: str = ""
    confidence: float = 0.0
    alternative_analyses: list[str] = field(default_factory=list)
    explanation: str = ""
    model_identity: str = ""  # e.g. "dicta-il/DictaLM-3.0-1.7B-Instruct"
    model_version: str = ""
    prompt_version: str = ""
    deterministic_engine_agreement: bool | None = None
    abstention_status: str = "abstain"  # accept, abstain, reject
    advisory_only: bool = True
    raw_response: str = ""
    parsed_json: dict[str, Any] = field(default_factory=dict)
    prompt_used: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "proposed_analysis": self.proposed_analysis,
            "confidence": self.confidence,
            "alternative_analyses": self.alternative_analyses,
            "explanation": self.explanation,
            "model_identity": self.model_identity,
            "model_version": self.model_version,
            "prompt_version": self.prompt_version,
            "deterministic_engine_agreement": self.deterministic_engine_agreement,
            "abstention_status": self.abstention_status,
            "advisory_only": self.advisory_only,
            "raw_response": self.raw_response,
            "parsed_json": self.parsed_json,
            "prompt_used": self.prompt_used,
        }


class _InferenceBackend(Protocol):
    """Pluggable backend for running a local model."""

    def generate(self, prompt: str, max_tokens: int, temperature: float, seed: int | None) -> str:
        ...


class HebrewEvaluatorAgent(ABC):
    """Abstract adviser for Hebrew linguistic tasks.

    Concrete adapters may load a model locally or call a server.  The base class
    enforces advisory-only behaviour: the ``advisory_only`` flag is always True
    and the result carries an ``abstention_status`` so that low-confidence or
    conflicting advice is ignored by downstream approval logic.
    """

    def __init__(self, model_identity: str, model_version: str, prompt_version: str = "1.0") -> None:
        self.model_identity = model_identity
        self.model_version = model_version
        self.prompt_version = prompt_version
        self._backend: _InferenceBackend | None = None

    @abstractmethod
    def _build_prompt(
        self,
        task: str,
        text: str,
        context: dict[str, Any],
        json_schema: dict[str, Any] | None = None,
    ) -> str:
        """Return the exact prompt string sent to the model."""

    @abstractmethod
    def _call_model(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> str:
        """Run inference and return raw text."""

    def evaluate(
        self,
        task: str,
        text: str,
        context: dict[str, Any] | None = None,
        deterministic_engine_result: dict[str, Any] | None = None,
    ) -> EvaluatorResult:
        """Run an advisory evaluation and compare with the deterministic engine."""
        ctx = context or {}
        schema = self._default_json_schema()
        prompt = self._build_prompt(task, text, ctx, schema)
        raw = self._call_model(prompt)
        parsed, confidence, abstain = self._parse_and_validate(raw, schema)

        agreement = self._compare_with_engine(parsed, deterministic_engine_result or {})

        return EvaluatorResult(
            proposed_analysis=parsed.get("analysis", ""),
            confidence=confidence,
            alternative_analyses=parsed.get("alternatives", []),
            explanation=parsed.get("explanation", ""),
            model_identity=self.model_identity,
            model_version=self.model_version,
            prompt_version=self.prompt_version,
            deterministic_engine_agreement=agreement,
            abstention_status="abstain" if (abstain or confidence < 0.6) else "accept",
            advisory_only=True,
            raw_response=raw,
            parsed_json=parsed,
            prompt_used=prompt,
        )

    def evaluate_sentence_naturalness(self, sentence: str, deterministic: dict[str, Any] | None = None) -> EvaluatorResult:
        return self.evaluate("sentence_naturalness", sentence, {}, deterministic)

    def disambiguate_morphology(self, form: str, candidates: list[dict[str, Any]], deterministic: dict[str, Any] | None = None) -> EvaluatorResult:
        return self.evaluate("morphological_disambiguation", form, {"candidates": candidates}, deterministic)

    def classify_register(self, sentence: str, deterministic: dict[str, Any] | None = None) -> EvaluatorResult:
        return self.evaluate("register_classification", sentence, {}, deterministic)

    def assess_semantic_plausibility(self, sentence: str, deterministic: dict[str, Any] | None = None) -> EvaluatorResult:
        return self.evaluate("semantic_plausibility", sentence, {}, deterministic)

    def diagnose_contextual_error(self, sentence: str, target_form: str, deterministic: dict[str, Any] | None = None) -> EvaluatorResult:
        return self.evaluate("contextual_error_diagnosis", sentence, {"target_form": target_form}, deterministic)

    def compare_variants(self, variants: list[str], context: dict[str, Any], deterministic: dict[str, Any] | None = None) -> EvaluatorResult:
        return self.evaluate("compare_accepted_variants", variants[0] if variants else "", {"variants": variants, **context}, deterministic)

    @staticmethod
    def _default_json_schema() -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "analysis": {"type": "string"},
                "confidence": {"type": "number"},
                "alternatives": {"type": "array", "items": {"type": "string"}},
                "explanation": {"type": "string"},
                "agrees_with_deterministic_engine": {"type": "boolean"},
                "abstain": {"type": "boolean"},
            },
            "required": ["analysis", "confidence", "abstain"],
        }

    def _parse_and_validate(self, raw: str, schema: dict[str, Any]) -> tuple[dict[str, Any], float, bool]:
        """Best-effort JSON extraction and validation."""
        parsed: dict[str, Any] = {}
        confidence = 0.0
        abstain = True

        # Try to extract a JSON object from the model output.
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[-1].split("```")[0].strip()

        # Find first JSON object.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                parsed = {}

        confidence = float(parsed.get("confidence", 0.0))
        abstain = bool(parsed.get("abstain", True))
        return parsed, max(0.0, min(1.0, confidence)), abstain

    def _compare_with_engine(self, parsed: dict[str, Any], engine_result: dict[str, Any]) -> bool | None:
        """Return whether the evaluator agrees with the deterministic engine."""
        if not engine_result:
            return None
        if "agrees_with_deterministic_engine" in parsed:
            return bool(parsed["agrees_with_deterministic_engine"])
        # Fallback: compare the analysis string to a simple engine summary.
        analysis = str(parsed.get("analysis", "")).lower()
        engine_key = str(engine_result.get("analysis", engine_result.get("status", ""))).lower()
        if not engine_key:
            return None
        return engine_key in analysis or analysis in engine_key


class DictaLMEvaluator(HebrewEvaluatorAgent):
    """Advisory evaluator backed by a DictaLM 3.0 model.

    Recommended default: ``dicta-il/DictaLM-3.0-1.7B-Instruct`` or one of the
    community MLX/GGUF conversions for local Apple-Silicon / edge inference.
    """

    def __init__(
        self,
        model_identity: str = "dicta-il/DictaLM-3.0-1.7B-Instruct",
        model_version: str = "3.0",
        backend: str = "auto",  # auto, mlx, transformers, llama_cpp, vllm
        model_path: Path | str | None = None,
    ) -> None:
        super().__init__(model_identity, model_version, prompt_version="1.0")
        self.backend = backend
        self.model_path = Path(model_path) if model_path else None
        self._mlx_model: Any = None
        self._mlx_tokenizer: Any = None
        self._llama_cpp_model: Any = None

    def _build_prompt(
        self,
        task: str,
        text: str,
        context: dict[str, Any],
        json_schema: dict[str, Any] | None = None,
    ) -> str:
        system = (
            "אתה עוזר לשוני לעברית מודרנית. ענה בקצרה ובאופן מובנה. "
            "אל תשנה או תאשר רשומות זהב אוטומטיות. התוצר שלך הוא ייעוצי בלבד. "
            "אם אינך בטוח, הגדר abstain=true."
        )
        user = (
            f"Task: {task}\n"
            f"Text: {text}\n"
            f"Context: {json.dumps(context, ensure_ascii=False, default=str)}\n\n"
            f"Return valid JSON matching this schema: {json.dumps(json_schema or self._default_json_schema(), ensure_ascii=False)}"
        )
        # HuggingFace chat template compatible format.
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return json.dumps(messages, ensure_ascii=False)

    def _call_model(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> str:
        backend = self._resolve_backend()
        if backend == "mlx":
            return self._call_mlx(prompt, max_tokens, temperature)
        if backend == "llama_cpp":
            return self._call_llama_cpp(prompt, max_tokens, temperature)
        if backend == "vllm":
            return self._call_vllm_openai(prompt, max_tokens, temperature)
        if backend == "transformers":
            return self._call_transformers(prompt, max_tokens, temperature)
        raise RuntimeError(f"No usable inference backend for {self.model_identity}")

    def _resolve_backend(self) -> str:
        if self.backend != "auto":
            return self.backend
        try:
            import mlx_lm  # noqa: F401
            return "mlx"
        except Exception:
            pass
        try:
            import llama_cpp  # noqa: F401
            return "llama_cpp"
        except Exception:
            pass
        try:
            import transformers  # noqa: F401
            return "transformers"
        except Exception:
            pass
        return "auto"

    def _call_mlx(self, prompt: str, max_tokens: int, temperature: float) -> str:
        from mlx_lm import generate, load

        if self._mlx_model is None:
            path = str(self.model_path) if self.model_path else self.model_identity
            self._mlx_model, self._mlx_tokenizer = load(path)
        model, tokenizer = self._mlx_model, self._mlx_tokenizer
        if tokenizer.chat_template:
            messages = json.loads(prompt)
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens, temp=temperature, verbose=False)

    def _call_llama_cpp(self, prompt: str, max_tokens: int, temperature: float) -> str:
        from llama_cpp import Llama

        if self._llama_cpp_model is None:
            path = str(self.model_path) if self.model_path else self.model_identity
            self._llama_cpp_model = Llama(model_path=path, n_ctx=4096, verbose=False)
        output = self._llama_cpp_model(prompt, max_tokens=max_tokens, temperature=temperature)
        return output["choices"][0]["text"]

    def _call_vllm_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        import os

        import openai

        client = openai.OpenAI(base_url=os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1"), api_key="no-key")
        messages = json.loads(prompt)
        response = client.chat.completions.create(
            model=self.model_identity,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def _call_transformers(self, prompt: str, max_tokens: int, temperature: float) -> str:
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        tokenizer = AutoTokenizer.from_pretrained(self.model_identity, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            self.model_identity,
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True,
        )
        messages = json.loads(prompt)
        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=max_tokens, temperature=temperature)
        out = pipe(messages)
        return out[0]["generated_text"][-1]["content"]


class HebatronEvaluator(HebrewEvaluatorAgent):
    """Advisory evaluator backed by a HEBATRON model.

    HEBATRON is much larger and requires high-end hardware.  The adapter is
    identical in contract to DictaLMEvaluator but defaults to the HEBATRON
    identifier and cautions about memory requirements.
    """

    def __init__(
        self,
        model_identity: str = "HebArabNlpProject/Hebatron",
        model_version: str = "1.0",
        backend: str = "auto",
        model_path: Path | str | None = None,
    ) -> None:
        super().__init__(model_identity, model_version, prompt_version="1.0")
        self.backend = backend
        self.model_path = Path(model_path) if model_path else None

    def _build_prompt(
        self,
        task: str,
        text: str,
        context: dict[str, Any],
        json_schema: dict[str, Any] | None = None,
    ) -> str:
        system = (
            "אתה עוזר לשוני לעברית מודרנית. התוצר שלך הוא ייעוצי בלבד ואינו משנה "
            "רשומות זהב אוטומטיות. אם אינך בטוח, הגדר abstain=true."
        )
        user = (
            f"Task: {task}\n"
            f"Text: {text}\n"
            f"Context: {json.dumps(context, ensure_ascii=False, default=str)}\n\n"
            f"Return valid JSON: {json.dumps(json_schema or self._default_json_schema(), ensure_ascii=False)}"
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return json.dumps(messages, ensure_ascii=False)

    def _call_model(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> str:
        # Re-use the same backend resolution/generation logic as DictaLM.
        # HEBATRON needs ``trust_remote_code=True`` and usually vLLM or a
        # pre-converted GGUF/MLX artifact.
        temp = DictaLMEvaluator(
            model_identity=self.model_identity,
            model_version=self.model_version,
            backend=self.backend,
            model_path=self.model_path,
        )
        return temp._call_model(prompt, max_tokens, temperature)


class MockEvaluator(HebrewEvaluatorAgent):
    """Deterministic mock for unit tests and CI."""

    def __init__(self, canned_response: str = "{}") -> None:
        super().__init__("mock", "0.0")
        self.canned_response = canned_response

    def _build_prompt(
        self,
        task: str,
        text: str,
        context: dict[str, Any],
        json_schema: dict[str, Any] | None = None,
    ) -> str:
        return json.dumps({"task": task, "text": text, "context": context}, ensure_ascii=False)

    def _call_model(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> str:
        return self.canned_response
