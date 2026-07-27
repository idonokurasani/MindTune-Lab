#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

APP = Path(__file__).resolve().parents[1]
OUT = APP / "data" / "pealim_hebrew_verbs.json"
BASE = "https://www.pealim.com"

NIQQUD_RE = re.compile(r"[\u0591-\u05bd\u05bf-\u05c7]")
TAG_RE = re.compile(r"<[^>]+>")

SEED_VERBS = [
    ("לאכול", "mangiare", "eat"),
    ("לשתות", "bere", "drink"),
    ("ללכת", "andare", "go"),
    ("לבוא", "venire", "come"),
    ("לעשות", "fare", "do"),
    ("לדבר", "parlare", "talk"),
    ("לכתוב", "scrivere", "write"),
    ("לקרוא", "leggere / chiamare", "read"),
    ("לשמוע", "sentire / ascoltare", "hear"),
    ("להקשיב", "ascoltare / prestare attenzione", "listen"),
    ("ללמוד", "studiare / imparare", "learn"),
    ("לעבוד", "lavorare", "work"),
    ("לראות", "vedere", "see"),
    ("לרצות", "volere", "want"),
    ("לדעת", "sapere", "know"),
    ("לתת", "dare", "give"),
    ("לקחת", "prendere", "take"),
    ("לקנות", "comprare", "buy"),
    ("להגיד", "dire", "say"),
    ("להיות", "essere", "be"),
    ("לישון", "dormire", "sleep"),
    ("לקום", "alzarsi", "get up"),
    ("לשבת", "sedersi / stare seduto", "sit"),
    ("לעמוד", "stare in piedi", "stand"),
    ("להיכנס", "entrare", "enter"),
    ("לצאת", "uscire", "exit"),
    ("לחזור", "tornare", "return"),
    ("לגור", "abitare", "live"),
    ("לשאול", "chiedere / domandare", "ask"),
    ("לענות", "rispondere", "answer"),
    ("לפתוח", "aprire", "open"),
    ("לסגור", "chiudere", "close"),
    ("להבין", "capire", "understand"),
    ("לזכור", "ricordare", "remember"),
    ("לשכוח", "dimenticare", "forget"),
    ("לעזור", "aiutare", "help"),
    ("לפגוש", "incontrare", "meet"),
    ("למצוא", "trovare", "find"),
    ("לאבד", "perdere", "lose"),
    ("להתחיל", "iniziare", "begin"),
    ("לסיים", "finire", "finish"),
    ("להמשיך", "continuare", "continue"),
    ("להפסיק", "smettere / interrompere", "stop"),
    ("לבחור", "scegliere", "choose"),
    ("לשלם", "pagare", "pay"),
    ("למכור", "vendere", "sell"),
    ("לאהוב", "amare", "love"),
    ("לשנוא", "odiare", "hate"),
    ("לחשוב", "pensare", "think"),
    ("להאמין", "credere", "believe"),
    ("להרגיש", "sentire / provare", "feel"),
    ("להצטרך", "avere bisogno", "need"),
    ("לשים", "mettere", "put"),
    ("להביא", "portare / portare qui", "bring"),
    ("לשלוח", "mandare / inviare", "send"),
    ("לקבל", "ricevere", "receive"),
    ("לנסוע", "viaggiare / andare in veicolo", "travel"),
    ("לטוס", "volare", "fly"),
    ("לנהוג", "guidare", "drive"),
    ("לרוץ", "correre", "run"),
]

FORM_IDS = {
    "present": {
        "ms": "AP-ms",
        "fs": "AP-fs",
        "mp": "AP-mp",
        "fp": "AP-fp",
    },
    "past": {
        "אני": "PERF-1s",
        "אתה": "PERF-2ms",
        "את": "PERF-2fs",
        "הוא": "PERF-3ms",
        "היא": "PERF-3fs",
        "אנחנו": "PERF-1p",
        "אתם": "PERF-2mp",
        "אתן": "PERF-2fp",
        "הם": "PERF-3p",
        "הן": "PERF-3p",
    },
    "future": {
        "אני": "IMPF-1s",
        "אתה": "IMPF-2ms",
        "את": "IMPF-2fs",
        "הוא": "IMPF-3ms",
        "היא": "IMPF-3fs",
        "אנחנו": "IMPF-1p",
        "אתם": "IMPF-2mp",
        "אתן": "IMPF-2fp",
        "הם": "IMPF-3mp",
        "הן": "IMPF-3fp",
    },
}

PERSON_IT = {
    "אני": "io",
    "אתה": "tu m.",
    "את": "tu f.",
    "הוא": "lui",
    "היא": "lei",
    "אנחנו": "noi",
    "אתם": "voi m.",
    "אתן": "voi f.",
    "הם": "loro m.",
    "הן": "loro f.",
}


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "MindTuneLab/3.17 Pealim cache builder"})
    with urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8", "ignore")


def strip_niqqud(value: str) -> str:
    value = html.unescape(value or "")
    value = TAG_RE.sub(" ", value)
    value = NIQQUD_RE.sub("", value)
    value = value.replace("־", "-").replace("\u200f", "").replace("!", "")
    value = value.replace("~", " ")
    return " ".join(value.split()).strip()


def first_dict_url(query: str, expected_en: str) -> str:
    search = f"{BASE}/search/?q={quote(query)}"
    text = fetch(search)
    candidates = []
    for match in re.finditer(
        r'<div class="verb-search-data">(.*?)<div class="verb-search-forms">', text, flags=re.S
    ):
        block = match.group(1)
        link_match = re.search(r'href="([^"]*/dict/[^"]+/)"', block)
        if not link_match:
            continue
        link = link_match.group(1)
        if any(skip in link for skip in ("/dict/prepositions/", "/dict/numerals/")):
            continue
        clean = " ".join(TAG_RE.sub(" ", html.unescape(block)).split()).casefold()
        candidates.append((urljoin(BASE, link), clean))
    if not candidates:
        raise RuntimeError(f"Pealim result not found for {query}")
    expected = expected_en.casefold().strip()
    if expected:
        for url, text_value in candidates:
            if expected in text_value:
                return url
    return candidates[0][0]


def extract_form(page: str, form_id: str) -> str:
    pattern = (
        r'id="' + re.escape(form_id) + r'".*?'
        r'<span class="menukad">([^<]+)</span>'
        r'(?:<span class="chaser">([^<]+)</span>)?'
    )
    match = re.search(pattern, page, flags=re.S)
    if not match:
        return ""
    menukad, chaser = match.groups()
    raw = chaser or menukad
    return strip_niqqud(raw)


def extract_meta(page: str) -> dict:
    description = ""
    match = re.search(r'<meta content="([^"]+)" name="description"', page)
    if match:
        description = html.unescape(match.group(1))
    root = ""
    binyan = ""
    root_match = re.search(r"Root:\s*([^|]+?)(?:The| \|)", description)
    if root_match:
        root = strip_niqqud(root_match.group(1).replace(" - ", "-"))
    binyan_match = re.search(r"Verb\s+–\s+([^|]+)", description)
    if binyan_match:
        binyan = binyan_match.group(1).strip()
    return {"description": description, "root": root, "binyan": binyan}


def build_entry(query: str, italian: str, expected_en: str, index: int) -> dict:
    url = first_dict_url(query, expected_en)
    page = fetch(url)
    meta = extract_meta(page)
    present = [
        extract_form(page, FORM_IDS["present"]["ms"]),
        extract_form(page, FORM_IDS["present"]["fs"]),
        extract_form(page, FORM_IDS["present"]["mp"]),
        extract_form(page, FORM_IDS["present"]["fp"]),
    ]
    infinitive = extract_form(page, "INF-L") or query
    targets = {}
    for tense_key, hebrew_tense, italian_tense in [
        ("past", "בעבר", "passato"),
        ("future", "בעתיד", "futuro"),
    ]:
        for person, form_id in FORM_IDS[tense_key].items():
            form = extract_form(page, form_id)
            if form:
                targets[f"{hebrew_tense} · {person}"] = [
                    form,
                    f"{PERSON_IT.get(person, person)} - {italian_tense}: {italian}",
                ]
    return {
        "id": f"pealim_{index:03d}",
        "source": "pealim",
        "source_url": url,
        "source_query": query,
        "source_expected_meaning_en": expected_en,
        "accessed_at": datetime.now(timezone.utc).isoformat(),
        "root": meta["root"],
        "binyan": meta["binyan"],
        "infinitive": infinitive,
        "displayInfinitive": infinitive,
        "infinitive_key": strip_niqqud(infinitive).replace(" ", ""),
        "italianInfinitive": italian,
        "italian": italian,
        "present": present,
        "targets": targets,
        "qa_status": "PEALIM_EXTRACTED",
        "qa_note": "Generated from Pealim page HTML; human spot-check still recommended.",
    }


def main() -> int:
    verbs = []
    failures = []
    for index, (query, italian, expected_en) in enumerate(SEED_VERBS, 1):
        try:
            verbs.append(build_entry(query, italian, expected_en, index))
            time.sleep(0.25)
        except Exception as exc:
            failures.append(
                {"query": query, "italian": italian, "expected_en": expected_en, "error": str(exc)}
            )
    payload = {
        "schema_version": "pealim_verb_cache_v1",
        "source": "Pealim Hebrew conjugation tables",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(verbs),
        "failures": failures,
        "verbs": verbs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} ({len(verbs)} verbs, {len(failures)} failures)")
    if failures:
        print(json.dumps(failures, ensure_ascii=False, indent=2))
    return 0 if verbs else 1


if __name__ == "__main__":
    raise SystemExit(main())
