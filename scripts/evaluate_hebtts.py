#!/usr/bin/env python3
"""Generate and evaluate HebTTS samples for the three approved verbs.

Does not integrate into MindTune Lab. Uses the HebTTS repo clone in
repos/HebTTS and its own isolated venv.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import List

import psutil
import soundfile as sf

APP = pathlib.Path(__file__).resolve().parents[1]
REPO = APP / "repos" / "HebTTS"
DATA = APP / "data" / "hebtts_eval"
AUDIO = DATA / "audio"
INPUTS = DATA / "inputs"
VENV_PYTHON = APP / ".venv_hebtts" / "bin" / "python"

os.makedirs(AUDIO, exist_ok=True)
os.makedirs(INPUTS, exist_ok=True)


def standard_unvocalized(row: dict) -> str:
    """Return the standard unvocalized spelling from Pealim row."""
    chaser = row.get("chaser", "").strip()
    if "~" in chaser:
        chaser = chaser.split("~", 1)[-1].strip()
    if chaser:
        return chaser
    return row.get("hebrew_without_niqqud", "")


def clean_transliteration(html_text: str) -> str:
    return html_text.replace("<b>", "").replace("</b>", "")


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def duration_of(path: pathlib.Path) -> float:
    data, sr = sf.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    return len(data) / sr


def run_infer(csv_path: pathlib.Path, output_dir: pathlib.Path, speaker: str = "osim", top_k: int = 40, mbd: bool = False) -> tuple[float, float, int]:
    """Run infer.py on a CSV. Returns (elapsed_seconds, peak_rss_mb, returncode)."""
    env = os.environ.copy()
    env["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"

    cmd = [
        str(VENV_PYTHON), "infer.py",
        "--checkpoint", "ckpt.pt",
        "--output-dir", str(output_dir),
        "--csv_path", str(csv_path),
        "--speaker", speaker,
        "--top-k", str(top_k),
    ]
    if mbd:
        cmd.extend(["--mbd", "True"])

    start = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        cwd=REPO,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    peak_mb = 0.0

    def monitor():
        nonlocal peak_mb
        try:
            p = psutil.Process(proc.pid)
        except psutil.NoSuchProcess:
            return
        while proc.poll() is None:
            try:
                children = p.children(recursive=True)
                mems = [child.memory_info().rss for child in children if child.is_running()] + [p.memory_info().rss]
                peak_mb = max(peak_mb, max(mems, default=0) / (1024 * 1024))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            time.sleep(0.5)

    mon = threading.Thread(target=monitor)
    mon.start()

    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

    rc = proc.wait()
    mon.join()
    elapsed = time.perf_counter() - start
    return elapsed, peak_mb, rc


def to_mp3(wav: pathlib.Path) -> pathlib.Path:
    mp3 = AUDIO / wav.with_suffix(".mp3").name
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav), "-q:a", "4", str(mp3)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return mp3


@dataclass
class Sample:
    verb: str
    form_key: str
    label: str
    text: str
    speaker: str = "osim"
    top_k: int = 40
    mbd: bool = False
    pealim_vocalized: str = ""
    pealim_transliteration: str = ""
    expected_stress: int = 0
    phonikud_override: str = ""
    input_type: str = "plain"
    notes: str = ""
    elapsed: float = 0.0
    peak_mb: float = 0.0
    output_wav: pathlib.Path = field(default_factory=pathlib.Path)
    output_mp3: pathlib.Path = field(default_factory=pathlib.Path)
    duration: float = 0.0
    rtf: float = 0.0
    sha256: str = ""
    status: str = "pending"
    returncode: int = 0


def build_samples(pealim_data: list, audit_data: list) -> List[Sample]:
    audit = {(r["verb"], r["form_key"]): r for r in audit_data}
    pealim = {}
    for v in pealim_data:
        for fk, row in v["forms"].items():
            pealim[(v["query"], fk)] = row

    samples: List[Sample] = []

    for verb_record in pealim_data:
        verb = verb_record["query"]
        forms = verb_record["forms"]
        chosen = ["infinitive", "present_masculine_singular", "past_1_singular", "future_1_singular"]
        for fk in chosen:
            if fk not in forms:
                continue
            p = forms[fk]
            a = audit.get((verb, fk), {})
            vocalized = p["hebrew_with_niqqud"]
            plain = standard_unvocalized(p)
            trans = clean_transliteration(p.get("transcription_html", ""))

            samples.append(Sample(
                verb=verb, form_key=fk, label=f"{fk}_plain", text=plain, input_type="plain",
                pealim_vocalized=vocalized, pealim_transliteration=trans,
                expected_stress=p.get("pealim_stress_syllable", 0),
                phonikud_override=a.get("manual_override", a.get("phonikud_phonemes", "")),
            ))
            # vocalized is expected to crash; handled in a dedicated one-sample batch
            samples.append(Sample(
                verb=verb, form_key=fk, label=f"{fk}_vocalized", text=vocalized, input_type="vocalized",
                pealim_vocalized=vocalized, pealim_transliteration=trans,
                expected_stress=p.get("pealim_stress_syllable", 0),
                phonikud_override=a.get("manual_override", a.get("phonikud_phonemes", "")),
                notes="expected to fail because tokenizer does not accept niqqud",
            ))

        # sentence
        if verb == "לכתוב":
            sentence_plain = "אני רוצה לכתוב"
            sentence_vocalized = "אֲנִי רוֹצֶה לִכְתֹּב"
        elif verb == "להיות":
            sentence_plain = "אני רוצה להיות"
            sentence_vocalized = "אֲנִי רוֹצֶה לִהְיוֹת"
        else:
            sentence_plain = "אני רוצה לעשות"
            sentence_vocalized = "אֲנִי רוֹצֶה לַעֲשׂוֹת"

        samples.append(Sample(verb=verb, form_key="sentence", label="sentence_plain", text=sentence_plain, input_type="sentence"))
        samples.append(Sample(verb=verb, form_key="sentence", label="sentence_vocalized", text=sentence_vocalized, input_type="sentence_vocalized", notes="vocalized sentence; expected crash"))

    # determinism / repeated / top-k on infinitive plain
    for i in range(3):
        samples.append(Sample(verb="לכתוב", form_key="infinitive", label=f"repeat_{i}", text="לכתוב", input_type="repeated"))
    for k in [1, 80]:
        samples.append(Sample(verb="לכתוב", form_key="infinitive", label=f"topk_{k}", text="לכתוב", top_k=k, input_type="topk"))

    # punctuation
    samples.append(Sample(verb="לכתוב", form_key="sentence", label="sentence_comma", text="אני רוצה לכתוב,", input_type="punctuation"))

    # phoneme input
    samples.append(Sample(verb="לכתוב", form_key="infinitive", label="phoneme_ipa", text="liχtˈov", input_type="phoneme", notes="IPA phonemes as text; expected to fail or produce noise"))

    return samples


def write_csv(path: pathlib.Path, samples: List[Sample]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["filename", "text"])
        for s in samples:
            s.output_wav = AUDIO / f"{s.verb}_{s.label}_spk-{s.speaker}_topk-{s.top_k}{'_mbd' if s.mbd else ''}.wav"
            w.writerow([s.output_wav.name, s.text])


def run_batch(samples: List[Sample], label: str) -> None:
    if not samples:
        return
    csv_path = INPUTS / f"batch_{label}.csv"
    write_csv(csv_path, samples)
    s = samples[0]
    print(f"\n=== {label}: speaker={s.speaker} top_k={s.top_k} mbd={s.mbd} n={len(samples)} ===")
    elapsed, peak, rc = run_infer(csv_path, AUDIO, speaker=s.speaker, top_k=s.top_k, mbd=s.mbd)
    print(f"Batch elapsed {elapsed:.1f}s, peak RAM {peak:.0f} MB, returncode {rc}")

    # Mark all with batch result; then check which files actually exist
    per = elapsed / max(len(samples), 1)
    for s in samples:
        s.returncode = rc
        s.elapsed = per
        s.peak_mb = peak
        if s.output_wav.exists():
            s.status = "generated"
            s.duration = duration_of(s.output_wav)
            s.rtf = elapsed / max(s.duration * len(samples), 0.001)
            s.sha256 = sha256_file(s.output_wav)
            s.output_mp3 = to_mp3(s.output_wav)
            if rc != 0:
                s.notes = f"process exited {rc} but file was produced"
        else:
            s.status = "failed"
            s.notes = (s.notes or "") + f" process exited {rc}"


def main() -> int:
    pealim_data = json.loads((APP / "data" / "phonikud_eval" / "pealim_forms.json").read_text(encoding="utf-8"))
    audit_data = json.loads((APP / "data" / "phonikud_eval" / "phonikud_evaluation.json").read_text(encoding="utf-8"))

    samples = build_samples(pealim_data, audit_data)

    # Plain + experiments that should work (no niqqud)
    plain_samples = [s for s in samples if "vocalized" not in s.input_type and s.input_type != "phoneme"]
    # Keep phoneme separate because it may crash; put punctuation/repeats/topk in the plain batch
    phoneme_samples = [s for s in samples if s.input_type == "phoneme"]
    vocalized_samples = [s for s in samples if "vocalized" in s.input_type]

    run_batch(plain_samples, "plain_and_experiments")
    run_batch(phoneme_samples, "phoneme")
    # Run just one vocalized sample to confirm crash
    if vocalized_samples:
        run_batch(vocalized_samples[:1], "vocalized_crash")
        for s in vocalized_samples[1:]:
            s.status = "skipped"
            s.notes = "vocalized inputs not attempted because tokenizer crashes on niqqud"

    # Speaker variations for infinitive plain (osim already in plain batch; add geek/shaul)
    infinitive_plain = [s for s in samples if s.form_key == "infinitive" and s.input_type == "plain"]
    speaker_samples = []
    for spk in ["geek", "shaul"]:
        for s in infinitive_plain:
            speaker_samples.append(Sample(
                verb=s.verb, form_key=s.form_key, label=f"{s.label}_spk-{spk}", text=s.text,
                speaker=spk, input_type="speaker_variation",
                pealim_vocalized=s.pealim_vocalized, pealim_transliteration=s.pealim_transliteration,
                expected_stress=s.expected_stress, phonikud_override=s.phonikud_override,
            ))
    run_batch(speaker_samples, "speaker_variations")

    # MBD attempt
    mbd_samples = [Sample(
        verb="לכתוב", form_key="infinitive", label="infinitive_plain_mbd", text="לכתוב",
        mbd=True, input_type="mbd", notes="Multi Band Diffusion; requires audiocraft",
    )]
    run_batch(mbd_samples, "mbd")

    all_samples = samples + speaker_samples + mbd_samples

    def as_dict(s: Sample) -> dict:
        return {
            "verb": s.verb, "form_key": s.form_key, "label": s.label,
            "input_type": s.input_type, "text": s.text, "speaker": s.speaker,
            "top_k": s.top_k, "mbd": s.mbd,
            "pealim_vocalized": s.pealim_vocalized,
            "pealim_transliteration": s.pealim_transliteration,
            "expected_stress": s.expected_stress,
            "phonikud_override": s.phonikud_override,
            "elapsed_seconds": s.elapsed,
            "peak_rss_mb": s.peak_mb,
            "duration_seconds": s.duration,
            "rtf": s.rtf,
            "sha256": s.sha256,
            "status": s.status,
            "returncode": s.returncode,
            "output_wav": str(s.output_wav) if s.output_wav else "",
            "output_mp3": str(s.output_mp3) if s.output_mp3 else "",
            "notes": s.notes,
        }

    json_path = DATA / "hebtts_evaluation.json"
    csv_path = DATA / "hebtts_evaluation.csv"
    json_path.write_text(json.dumps([as_dict(s) for s in all_samples], ensure_ascii=False, indent=2), encoding="utf-8")

    keys = list(as_dict(all_samples[0]).keys())
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(as_dict(s) for s in all_samples)

    print(f"\nWrote {csv_path} and {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
