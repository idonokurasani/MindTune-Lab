#!/usr/bin/env python3
"""Fetch Pealim pages for 3 verbs and extract menukad, chaser, transcription, stress."""
from __future__ import annotations

import html
import json
import re
import time
from pathlib import Path
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

APP = Path(__file__).resolve().parents[1]
OUT = APP / "data" / "phonikud_eval" / "pealim_forms.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
BASE = "https://www.pealim.com"

FORM_IDS = {
    "infinitive": "INF-L",
    "present_masculine_singular": "AP-ms",
    "present_feminine_singular": "AP-fs",
    "present_masculine_plural": "AP-mp",
    "present_feminine_plural": "AP-fp",
    "past_1_singular": "PERF-1s",
    "past_2_masculine_singular": "PERF-2ms",
    "past_2_feminine_singular": "PERF-2fs",
    "past_3_masculine_singular": "PERF-3ms",
    "past_3_feminine_singular": "PERF-3fs",
    "past_1_plural": "PERF-1p",
    "past_2_masculine_plural": "PERF-2mp",
    "past_2_feminine_plural": "PERF-2fp",
    "past_3_plural": "PERF-3p",
    "future_1_singular": "IMPF-1s",
    "future_2_masculine_singular": "IMPF-2ms",
    "future_2_feminine_singular": "IMPF-2fs",
    "future_3_masculine_singular": "IMPF-3ms",
    "future_3_feminine_singular": "IMPF-3fs",
    "future_1_plural": "IMPF-1p",
    "future_2_plural": "IMPF-2mp",
    "future_3_plural": "IMPF-3mp",
}

def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "MindTuneLab/3.17 Pealim phoneme extractor"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

def stress_from_transcription(t: str) -> int:
    before, _, _ = t.partition("<b>")
    return len(re.findall(r"[aeiou]", before.lower())) + 1

def _find_in_window(page: str, start_pos: int, end_pos: int, pattern: str) -> str | None:
    m = re.search(pattern, page[start_pos:end_pos], re.S)
    return m.group(1) if m else None


def extract_form(page: str, fid: str) -> dict | None:
    m = re.search(rf'id="{fid}"[^>]*>', page)
    if not m:
        return None
    start = m.end()
    end = start + 600
    menukad_raw = _find_in_window(page, start, end, r'<span class="menukad">([^<]+)</span>')
    if not menukad_raw:
        return None
    menukad = html.unescape(menukad_raw)
    chaser_raw = _find_in_window(page, start, end, r'<span class="chaser">([^<]+)</span>')
    chaser = html.unescape(chaser_raw) if chaser_raw else ""
    trans_raw = _find_in_window(page, start, end, r'<div class="transcription">(.*?)</div>')
    transcription = trans_raw or ""
    stress = stress_from_transcription(transcription) if transcription else 0
    return {
        "hebrew_with_niqqud": menukad,
        "hebrew_without_niqqud": re.sub(r"[\u0591-\u05bd\u05bf-\u05c7]", "", menukad).strip(),
        "chaser": chaser,
        "transcription_html": transcription,
        "pealim_stress_syllable": stress,
    }

def extract_meta(page: str) -> dict:
    root = binyan = ""
    m = re.search(r'<meta content="([^"]+)" name="description"', page)
    desc = html.unescape(m.group(1)) if m else ""
    rm = re.search(r"Root:\s*([^|]+?)(?:The| \|)", desc)
    if rm:
        root = re.sub(r"<[^>]+>", "", rm.group(1)).replace(" - ", "-").strip()
    bm = re.search(r"Verb\s+–\s+([^|]+)", desc)
    if bm:
        binyan = bm.group(1).strip()
    return {"root": root, "binyan": binyan, "description": desc}

def search_url(query: str) -> str:
    text = fetch(f"{BASE}/search/?q={quote(query)}")
    for match in re.finditer(r'<div class="verb-search-data">(.*?)<div class="verb-search-forms">', text, re.S):
        link = re.search(r'href="([^"]*dict/[^"]+/)"', match.group(1))
        if not link:
            continue
        href = link.group(1)
        if any(skip in href for skip in ("/dict/prepositions/", "/dict/numerals/")):
            continue
        return urljoin(BASE, href)
    raise RuntimeError(f"No Pealim result for {query}")

def build_verb(query: str) -> dict:
    url = search_url(query)
    page = fetch(url)
    meta = extract_meta(page)
    out = {"query": query, "source_url": url, "root": meta["root"], "binyan": meta["binyan"]}
    forms = {}
    for key, fid in FORM_IDS.items():
        f = extract_form(page, fid)
        if f:
            forms[key] = f
    out["forms"] = forms
    return out

def main() -> int:
    verbs = ["לכתוב", "להיות", "לעשות"]
    data = []
    for v in verbs:
        print("Fetching", v)
        data.append(build_verb(v))
        time.sleep(0.5)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", OUT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
