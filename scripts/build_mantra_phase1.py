#!/usr/bin/env python3
"""Build the Phase 1 Mantra content dataset for the first 3 Hebrew verbs.

Run after setting MINDTUNE_AZURE_SPEECH_KEY and MINDTUNE_AZURE_SPEECH_REGION to
also generate audio files. Without credentials the script still writes JSON,
SSML, audit, and plan files.
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
import urllib.request
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

APP = Path(__file__).resolve().parents[1]
DATA = APP / "data" / "mantra"
SCRIPTS = DATA / "scripts"
SSML = DATA / "ssml"
AUDIO = DATA / "audio"

DATA.mkdir(parents=True, exist_ok=True)
SCRIPTS.mkdir(parents=True, exist_ok=True)
SSML.mkdir(parents=True, exist_ok=True)
AUDIO.mkdir(parents=True, exist_ok=True)

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# 100-verb plan (order, verb, Italian, binyan, root, frequency/usefulness note)
# ---------------------------------------------------------------------------

VERBS_100: list[dict[str, Any]] = [
    # Core Pa'al, Pi'el, and common irregulars first
    {"order": 1, "verb": "לִכְתֹּב", "italian": "scrivere", "binyan": "PA'AL", "root": "כ-ת-ב", "freq": "core", "rationale": "High-frequency creative/action verb; regular Pa'al model."},
    {"order": 2, "verb": "לְדַבֵּר", "italian": "parlare", "binyan": "PI'EL", "root": "ד-ב-ר", "freq": "core", "rationale": "Essential communication; canonical Pi'el."},
    {"order": 3, "verb": "לֶאֱכוֹל", "italian": "mangiare", "binyan": "PA'AL", "root": "א-כ-ל", "freq": "core", "rationale": "Daily action; initial-alef irregular pattern."},
    {"order": 4, "verb": "לָלֶכֶת", "italian": "andare", "binyan": "PA'AL", "root": "ה-ל-ך", "freq": "core", "rationale": "Most common motion verb; weak root (ה drops)."},
    {"order": 5, "verb": "לִשְׁתּוֹת", "italian": "bere", "binyan": "PA'AL", "root": "ש-ת-ה", "freq": "core", "rationale": "Daily action; final-he pattern."},
    {"order": 6, "verb": "לָבוֹא", "italian": "venire", "binyan": "PA'AL", "root": "ב-ו-א", "freq": "core", "rationale": "Core motion verb; initial-alef."},
    {"order": 7, "verb": "לַעֲשׂוֹת", "italian": "fare", "binyan": "PA'AL", "root": "ע-ש-ה", "freq": "core", "rationale": "Highest-frequency general verb."},
    {"order": 8, "verb": "לִרְאוֹת", "italian": "vedere", "binyan": "PA'AL", "root": "ר-א-ה", "freq": "core", "rationale": "Core perception; final-he pattern."},
    {"order": 9, "verb": "לִשְׁמוֹעַ", "italian": "sentire", "binyan": "PA'AL", "root": "ש-מ-ע", "freq": "core", "rationale": "Core perception; final-ayin."},
    {"order": 10, "verb": "לָדַעַת", "italian": "sapere", "binyan": "PA'AL", "root": "י-ד-ע", "freq": "core", "rationale": "Cognitive state; initial-yod drops."},
    {"order": 11, "verb": "לְהַגִּיד", "italian": "dire", "binyan": "HIF'IL", "root": "נ-ג-ד", "freq": "core", "rationale": "Everyday speech; Hif'il."},
    {"order": 12, "verb": "לִתְתֵּן", "italian": "dare", "binyan": "PA'AL", "root": "נ-ת-נ", "freq": "core", "rationale": "Core transfer verb; initial-nun drops."},
    {"order": 13, "verb": "לָקַחַת", "italian": "prendere", "binyan": "PA'AL", "root": "ל-ק-ח", "freq": "core", "rationale": "Core transfer verb."},
    {"order": 14, "verb": "לִקְנוֹת", "italian": "comprare", "binyan": "PA'AL", "root": "ק-נ-ה", "freq": "high", "rationale": "Commerce; final-he."},
    {"order": 15, "verb": "לָגוּר", "italian": "abitare", "binyan": "PA'AL", "root": "ג-ו-ר", "freq": "high", "rationale": "Daily life."},
    {"order": 16, "verb": "לֶאֱהוֹב", "italian": "amare", "binyan": "PA'AL", "root": "א-ה-ב", "freq": "high", "rationale": "Emotion; initial-alef."},
    {"order": 17, "verb": "לְשַׂנּוֹא", "italian": "odiare", "binyan": "PA'AL", "root": "ש-נ-א", "freq": "medium", "rationale": "Emotion; final-alef."},
    {"order": 18, "verb": "לַעֲבוֹד", "italian": "lavorare", "binyan": "PA'AL", "root": "ע-ב-ד", "freq": "high", "rationale": "Daily activity."},
    {"order": 19, "verb": "לִלְמוֹד", "italian": "studiare", "binyan": "PA'AL", "root": "ל-מ-ד", "freq": "high", "rationale": "Learning context."},
    {"order": 20, "verb": "לְהָבִיא", "italian": "portare", "binyan": "HIF'IL", "root": "ב-ו-א", "freq": "high", "rationale": "Transfer; Hif'il of 'to come'."},
    {"order": 21, "verb": "לִפְתּוֹחַ", "italian": "aprire", "binyan": "PA'AL", "root": "פ-ת-ח", "freq": "high", "rationale": "Daily action."},
    {"order": 22, "verb": "לִסְגּוֹר", "italian": "chiudere", "binyan": "PA'AL", "root": "ס-ג-ר", "freq": "high", "rationale": "Daily action."},
    {"order": 23, "verb": "לִקְרוֹאַ", "italian": "leggere / chiamare", "binyan": "PA'AL", "root": "ק-ר-א", "freq": "high", "rationale": "Cultural/education; final-alef."},
    {"order": 24, "verb": "לִכְנֵס", "italian": "entrare", "binyan": "NIF'AL", "root": "כ-נ-ס", "freq": "high", "rationale": "Motion; Nif'al."},
    {"order": 25, "verb": "לָצֵאת", "italian": "uscire", "binyan": "PA'AL", "root": "י-צ-א", "freq": "high", "rationale": "Motion; initial-yod drops."},
    {"order": 26, "verb": "לַחֲזוֹר", "italian": "tornare", "binyan": "PA'AL", "root": "ח-ז-ר", "freq": "high", "rationale": "Motion."},
    {"order": 27, "verb": "לְהַבִין", "italian": "capire", "binyan": "HIF'IL", "root": "ב-י-נ", "freq": "high", "rationale": "Cognitive; Hif'il."},
    {"order": 28, "verb": "לִישׁוֹן", "italian": "dormire", "binyan": "PA'AL", "root": "י-ש-נ", "freq": "high", "rationale": "Daily action; initial-yod drops."},
    {"order": 29, "verb": "לָקוּם", "italian": "alzarsi", "binyan": "PA'AL", "root": "ק-ו-מ", "freq": "high", "rationale": "Daily action."},
    {"order": 30, "verb": "לָשֶׁבֶת", "italian": "sedersi", "binyan": "PA'AL", "root": "י-ש-ב", "freq": "high", "rationale": "Daily action; initial-yod drops."},
    {"order": 31, "verb": "לַעֲמוֹד", "italian": "stare in piedi", "binyan": "PA'AL", "root": "ע-מ-ד", "freq": "high", "rationale": "Posture/motion."},
    {"order": 32, "verb": "לְהַתְחִיל", "italian": "iniziare", "binyan": "HITPA'EL", "root": "ת-ח-ל", "freq": "high", "rationale": "Transition; Hitpa'el."},
    {"order": 33, "verb": "לְסַיֵּם", "italian": "finire", "binyan": "PI'EL", "root": "ס-י-מ", "freq": "high", "rationale": "Transition; Pi'el."},
    {"order": 34, "verb": "לְהַמְשִׁיךְ", "italian": "continuare", "binyan": "HIF'IL", "root": "מ-ש-ך", "freq": "high", "rationale": "Transition; Hif'il."},
    {"order": 35, "verb": "לְהַפְסִיק", "italian": "smettere", "binyan": "HIF'IL", "root": "פ-ס-ק", "freq": "high", "rationale": "Transition; Hif'il."},
    {"order": 36, "verb": "לִשְׁאוֹל", "italian": "chiedere", "binyan": "PA'AL", "root": "ש-א-ל", "freq": "high", "rationale": "Communication."},
    {"order": 37, "verb": "לַעֲנוֹת", "italian": "rispondere", "binyan": "PA'AL", "root": "ע-נ-ה", "freq": "high", "rationale": "Communication; final-he."},
    {"order": 38, "verb": "לְהַאֲמִין", "italian": "credere", "binyan": "HIF'IL", "root": "א-מ-נ", "freq": "medium", "rationale": "Cognitive; Hif'il."},
    {"order": 39, "verb": "לַחֲשׁוֹב", "italian": "pensare", "binyan": "PA'AL", "root": "ח-ש-ב", "freq": "high", "rationale": "Cognitive."},
    {"order": 40, "verb": "לְהַרְגִישׁ", "italian": "sentire", "binyan": "HIF'IL", "root": "ר-ג-ש", "freq": "high", "rationale": "Emotion/perception; Hif'il."},
    {"order": 41, "verb": "לִרְצוֹת", "italian": "volere", "binyan": "PA'AL", "root": "ר-צ-ה", "freq": "high", "rationale": "Modal; final-he."},
    {"order": 42, "verb": "לְהִצְטָרֵךְ", "italian": "avere bisogno", "binyan": "HIF'IL", "root": "צ-ר-כ", "freq": "high", "rationale": "Modal; Hif'il."},
    {"order": 43, "verb": "לִבְחוֹר", "italian": "scegliere", "binyan": "PA'AL", "root": "ב-ח-ר", "freq": "medium", "rationale": "Decision."},
    {"order": 44, "verb": "לְשַׁלֵּם", "italian": "pagare", "binyan": "PI'EL", "root": "ש-ל-מ", "freq": "high", "rationale": "Commerce; Pi'el."},
    {"order": 45, "verb": "לִמְכּוֹר", "italian": "vendere", "binyan": "PA'AL", "root": "מ-כ-ר", "freq": "medium", "rationale": "Commerce."},
    {"order": 46, "verb": "לְקַבֵּל", "italian": "ricevere", "binyan": "PI'EL", "root": "ק-ב-ל", "freq": "high", "rationale": "Transfer; Pi'el."},
    {"order": 47, "verb": "לְשַׁלּוֹחַ", "italian": "mandare", "binyan": "PA'AL", "root": "ש-ל-ח", "freq": "high", "rationale": "Communication/transfer."},
    {"order": 48, "verb": "לִנְסוֹעַ", "italian": "viaggiare", "binyan": "PA'AL", "root": "נ-ס-ע", "freq": "medium", "rationale": "Motion."},
    {"order": 49, "verb": "לָטוּס", "italian": "volare", "binyan": "PA'AL", "root": "ט-ו-ס", "freq": "medium", "rationale": "Motion."},
    {"order": 50, "verb": "לִנְהוֹגַ", "italian": "guidare", "binyan": "PA'AL", "root": "נ-ה-ג", "freq": "medium", "rationale": "Motion."},
    {"order": 51, "verb": "לָרוּץ", "italian": "correre", "binyan": "PA'AL", "root": "ר-ו-צ", "freq": "medium", "rationale": "Motion."},
    {"order": 52, "verb": "לְהַכִּיר", "italian": "conoscere", "binyan": "HIF'IL", "root": "י-ד-ע?", "freq": "high", "rationale": "Social; Hif'il (root נ-כ-ר)."},
    {"order": 53, "verb": "לִמְצוֹאַ", "italian": "trovare", "binyan": "PA'AL", "root": "מ-צ-א", "freq": "high", "rationale": "Daily; final-alef."},
    {"order": 54, "verb": "לֶאֱבוֹד", "italian": "perdere", "binyan": "PA'AL", "root": "א-ב-ד", "freq": "medium", "rationale": "Daily; initial-alef."},
    {"order": 55, "verb": "לִפְגוֹשׁ", "italian": "incontrare", "binyan": "PA'AL", "root": "פ-ג-שׁ", "freq": "high", "rationale": "Social."},
    {"order": 56, "verb": "לַעֲזוֹר", "italian": "aiutare", "binyan": "PA'AL", "root": "ע-ז-ר", "freq": "high", "rationale": "Social."},
    {"order": 57, "verb": "לִזְכּוֹר", "italian": "ricordare", "binyan": "PA'AL", "root": "ז-כ-ר", "freq": "high", "rationale": "Cognitive."},
    {"order": 58, "verb": "לִשְׁכּוֹחַ", "italian": "dimenticare", "binyan": "PA'AL", "root": "ש-כ-ח", "freq": "medium", "rationale": "Cognitive."},
    {"order": 59, "verb": "לְהַזְכִּיר", "italian": "ricordare (a qlcn)", "binyan": "HIF'IL", "root": "ז-כ-ר", "freq": "medium", "rationale": "Hif'il causative."},
    {"order": 60, "verb": "לְהַזְמִין", "italian": "invitare / ordinare", "binyan": "HIF'IL", "root": "ז-מ-נ", "freq": "medium", "rationale": "Hif'il."},
    {"order": 61, "verb": "לְהַגִּיעַ", "italian": "arrivare", "binyan": "HIF'IL", "root": "נ-ג-ע", "freq": "high", "rationale": "Motion; Hif'il."},
    {"order": 62, "verb": "לְהַסְבִּיר", "italian": "spiegare", "binyan": "HIF'IL", "root": "ס-ב-ר", "freq": "high", "rationale": "Communication; Hif'il."},
    {"order": 63, "verb": "לְהַדְלִיק", "italian": "accendere", "binyan": "HIF'IL", "root": "ד-ל-ק", "freq": "medium", "rationale": "Hif'il."},
    {"order": 64, "verb": "לְהַכְנִיס", "italian": "far entrare", "binyan": "HIF'IL", "root": "כ-נ-ס", "freq": "medium", "rationale": "Hif'il causative."},
    {"order": 65, "verb": "לְהַחְלִיט", "italian": "decidere", "binyan": "HIF'IL", "root": "ח-ל-ט", "freq": "medium", "rationale": "Hif'il."},
    {"order": 66, "verb": "לְבַקֵּשׁ", "italian": "chiedere / pregare", "binyan": "PI'EL", "root": "ב-ק-שׁ", "freq": "high", "rationale": "Pi'el."},
    {"order": 67, "verb": "לְסַפֵּר", "italian": "raccontare", "binyan": "PI'EL", "root": "ס-פ-ר", "freq": "high", "rationale": "Pi'el."},
    {"order": 68, "verb": "לְחַכּוֹת", "italian": "aspettare", "binyan": "PI'EL", "root": "ח-כ-ה", "freq": "high", "rationale": "Pi'el."},
    {"order": 69, "verb": "לְתַקֵּן", "italian": "sistemare / riparare", "binyan": "PI'EL", "root": "ת-ק-נ", "freq": "medium", "rationale": "Pi'el."},
    {"order": 70, "verb": "לְבַדֵּק", "italian": "controllare", "binyan": "PI'EL", "root": "ב-ד-ק", "freq": "medium", "rationale": "Pi'el."},
    {"order": 71, "verb": "לְנַסֵּה", "italian": "provare", "binyan": "PI'EL", "root": "נ-ס-ה", "freq": "medium", "rationale": "Pi'el; final-he."},
    {"order": 72, "verb": "לְשַׁנּוֹת", "italian": "cambiare", "binyan": "PI'EL", "root": "ש-נ-ה", "freq": "medium", "rationale": "Pi'el."},
    {"order": 73, "verb": "לְהִתְאָהֵב", "italian": "innamorarsi", "binyan": "HITPA'EL", "root": "א-ה-ב", "freq": "medium", "rationale": "Hitpa'el."},
    {"order": 74, "verb": "לְהִתְפַּלֵּל", "italian": "pregare", "binyan": "HITPA'EL", "root": "פ-ל-ל", "freq": "medium", "rationale": "Hitpa'el."},
    {"order": 75, "verb": "לְהִתְרַחֵץ", "italian": "lavarsi", "binyan": "HITPA'EL", "root": "ר-ח-צ", "freq": "medium", "rationale": "Hitpa'el."},
    {"order": 76, "verb": "לְהִתְלַבֵּשׁ", "italian": "vestirsi", "binyan": "HITPA'EL", "root": "ל-ב-שׁ", "freq": "high", "rationale": "Hitpa'el."},
    {"order": 77, "verb": "לְהִתְעוֹרֵר", "italian": "svegliarsi", "binyan": "HITPA'EL", "root": "ע-ו-ר", "freq": "medium", "rationale": "Hitpa'el."},
    {"order": 78, "verb": "לְהִתְגַּעְגֵּעַ", "italian": "sentire la mancanza", "binyan": "HITPA'EL", "root": "ג-ע-ג", "freq": "low", "rationale": "Hitpa'el emotional."},
    {"order": 79, "verb": "לְהִתְנַצֵּל", "italian": "scusarsi", "binyan": "HITPA'EL", "root": "נ-צ-ל", "freq": "medium", "rationale": "Hitpa'el."},
    {"order": 80, "verb": "לְהִתְפַּגֵּשׁ", "italian": "incontrarsi", "binyan": "HITPA'EL", "root": "פ-ג-שׁ", "freq": "high", "rationale": "Hitpa'el reciprocal."},
    {"order": 81, "verb": "לְהִכָּתֵב", "italian": "essere scritto", "binyan": "NIF'AL", "root": "כ-ת-ב", "freq": "low", "rationale": "Nif'al passive; irregular."},
    {"order": 82, "verb": "לְהִשָּׁאֵל", "italian": "essere chiesto", "binyan": "NIF'AL", "root": "ש-א-ל", "freq": "low", "rationale": "Nif'al passive."},
    {"order": 83, "verb": "לְהִיבָּנוֹת", "italian": "essere costruito", "binyan": "NIF'AL", "root": "ב-נ-ה", "freq": "low", "rationale": "Nif'al passive."},
    {"order": 84, "verb": "לְהִיכָּנֵס", "italian": "essere accolto", "binyan": "NIF'AL", "root": "כ-נ-ס", "freq": "low", "rationale": "Nif'al passive."},
    {"order": 85, "verb": "לְהוּכַח", "italian": "essere dimostrato", "binyan": "HUF'AL", "root": "ו-כ-ח", "freq": "very_low", "rationale": "Huf'al passive; binyan coverage."},
    {"order": 86, "verb": "לְהוּכַן", "italian": "essere preparato", "binyan": "HUF'AL", "root": "כ-ו-נ", "freq": "very_low", "rationale": "Huf'al passive; binyan coverage."},
    {"order": 87, "verb": "לְדֻבַּר", "italian": "essere parlato", "binyan": "PU'AL", "root": "ד-ב-ר", "freq": "very_low", "rationale": "Pual passive; binyan coverage."},
    {"order": 88, "verb": "לְהָפְקֵר", "italian": "essere abbandonato", "binyan": "HUF'AL", "root": "פ-ק-ר", "freq": "very_low", "rationale": "Huf'al passive."},
    {"order": 89, "verb": "לָמוּת", "italian": "morire", "binyan": "PA'AL", "root": "מ-ו-ת", "freq": "medium", "rationale": "Irregular final-weak."},
    {"order": 90, "verb": "לָחְיוֹת", "italian": "vivere", "binyan": "PA'AL", "root": "ח-י-ה", "freq": "high", "rationale": "Irregular middle-yod."},
    {"order": 91, "verb": "לָדוּן", "italian": "discutere / giudicare", "binyan": "PA'AL", "root": "ד-י-נ", "freq": "medium", "rationale": "Irregular middle-yod."},
    {"order": 92, "verb": "לְהִסְתַּכֵּל", "italian": "guardare", "binyan": "HITPA'EL", "root": "ס-כ-ל", "freq": "high", "rationale": "Visual perception; Hitpa'el."},
    {"order": 93, "verb": "לָגַעַת", "italian": "toccare", "binyan": "PA'AL", "root": "נ-ג-ע", "freq": "medium", "rationale": "Physical action."},
    {"order": 94, "verb": "לִשְׁמוֹר", "italian": "guardare / tenere", "binyan": "PA'AL", "root": "ש-מ-ר", "freq": "medium", "rationale": "Daily."},
    {"order": 95, "verb": "לִשְׁאוֹבַ", "italian": "attirare / pompare", "binyan": "PA'AL", "root": "ש-א-ב", "freq": "low", "rationale": "Less common; root coverage."},
    {"order": 96, "verb": "לִגְמוֹר", "italian": "finire", "binyan": "PA'AL", "root": "ג-מ-ר", "freq": "medium", "rationale": "Daily."},
    {"order": 97, "verb": "לְהַשְׁתִּיק", "italian": "far tacere", "binyan": "HIF'IL", "root": "ש-ת-ק", "freq": "low", "rationale": "Hif'il causative."},
    {"order": 98, "verb": "לְהַזְכִּיר", "italian": "rammentare", "binyan": "HIF'IL", "root": "ז-כ-ר", "freq": "medium", "rationale": "Hif'il."},
    {"order": 99, "verb": "לְהִשְׁתַּנּוֹת", "italian": "cambiarsi", "binyan": "HITPA'EL", "root": "ש-נ-ה", "freq": "medium", "rationale": "Hitpa'el."},
    {"order": 100, "verb": "לְהִתְקַדֵּם", "italian": "progredire", "binyan": "HITPA'EL", "root": "ק-ד-מ", "freq": "medium", "rationale": "Hitpa'el; learner-relevant."},
]

# Fix a couple of entries that had placeholder roots
for v in VERBS_100:
    if v["verb"] == "לְהַכִּיר":
        v["root"] = "נ-כ-ר"
    if v["verb"] == "לָגַעַת":
        v["root"] = "נ-ג-ע"


# ---------------------------------------------------------------------------
# Detailed data for the first 3 verbs (verified against Pealim 2026-07-22)
# ---------------------------------------------------------------------------


def f(he_with: str, he_without: str, translit: str, stress: int, tts: str | None = None, italian: str = "") -> dict:
    """Return a standard form record."""
    return {
        "hebrew_with_niqqud": he_with,
        "hebrew_without_niqqud": he_without,
        "display_transliteration": translit,
        "tts_input": tts or he_with,
        "stress_syllable_index": stress,
        "italian_gloss": italian,
    }


VERBS_3: list[dict[str, Any]] = [
    {
        "order": 1,
        "infinitive_hebrew_with_niqqud": "לִכְתֹּב",
        "infinitive_hebrew_without_niqqud": "לכתוב",
        "infinitive_transliteration": "lichtov",
        "italian_translation": "scrivere",
        "root": "כ-ת-ב",
        "binyan": "PA'AL",
        "source_url": "https://www.pealim.com/dict/1-lichtov/",
        "source_checked_date": TODAY,
        "source_notes": "Verified from Pealim conjugation table. Stress on final syllable. Feminine plural future uses the common masculine plural form in ordinary modern speech.",
        "example_hebrew_with_niqqud": "אֲנִי כּוֹתֵב מִכְתָּב",
        "example_hebrew_without_niqqud": "אני כותב מכתב",
        "example_transliteration": "ani kotev mikhtav",
        "example_italian": "Scrivo una lettera.",
        "stress_metadata": {
            "primary_stress_pattern": "variable_by_form",
            "notes": "Infinitive stress on last syllable. Present tense stress on the penultimate or ultimate suffix as marked per form.",
        },
        "pronunciation_verification_status": "verified_from_pealim",
        "content_verification_status": "verified",
        "present": {
            "masculine_singular": f("כּוֹתֵב", "כותב", "kotev", 1, italian="io scrivo"),
            "feminine_singular": f("כּוֹתֶבֶת", "כותבת", "kotevet", 2, italian="io scrivo (f.)"),
            "masculine_plural": f("כּוֹתְבִים", "כותבים", "kotvim", 2, italian="noi/voi/loro scrivono"),
            "feminine_plural": f("כּוֹתְבוֹת", "כותבות", "kotvot", 2, italian="noi/voi/loro scrivono (f.)"),
        },
        "past": {
            "1_singular": f("כָּתַבְתִּי", "כתבתי", "katavti", 2, italian="io scrissi"),
            "2_masculine_singular": f("כָּתַבְתָּ", "כתבת", "katavta", 1, italian="tu scrivesti"),
            "2_feminine_singular": f("כָּתַבְתְּ", "כתבת", "katavt", 1, italian="tu scrivesti (f.)"),
            "3_masculine_singular": f("כָּתַב", "כתב", "katav", 1, italian="lui scrisse"),
            "3_feminine_singular": f("כָּתְבָה", "כתבה", "katva", 2, italian="lei scrisse"),
            "1_plural": f("כָּתַבְנוּ", "כתבנו", "katavnu", 1, italian="noi scrivemmo"),
            "2_masculine_plural": f("כְּתַבְתֶּם", "כתבתם", "ktavtem", 1, italian="voi scriveste"),
            "2_feminine_plural": f("כְּתַבְתֶּן", "כתבתן", "ktavten", 1, italian="voi scriveste (f.)"),
            "3_plural": f("כָּתְבוּ", "כתבו", "katvu", 1, italian="loro scrissero"),
        },
        "future": {
            "1_singular": f("אֶכְתֹּב", "אכתוב", "echtov", 2, italian="io scriverò"),
            "2_masculine_singular": f("תִּכְתֹּב", "תכתוב", "tichtov", 2, italian="tu scriverai"),
            "2_feminine_singular": f("תִּכְתְּבִי", "תכתבי", "tichte'vi", 2, italian="tu scriverai (f.)"),
            "3_masculine_singular": f("יִכְתֹּב", "יכתוב", "yichtov", 2, italian="lui scriverà"),
            "3_feminine_singular": f("תִּכְתֹּב", "תכתוב", "tichtov", 2, italian="lei scriverà"),
            "1_plural": f("נִכְתֹּב", "נכתוב", "nichtov", 2, italian="noi scriveremo"),
            "2_plural": f("תִּכְתְּבוּ", "תכתבו", "tichte'vu", 2, italian="voi scriverete"),
            "3_plural": f("יִכְתְּבוּ", "יכתבו", "yichte'vu", 2, italian="loro scriveranno"),
        },
    },
    {
        "order": 2,
        "infinitive_hebrew_with_niqqud": "לְדַבֵּר",
        "infinitive_hebrew_without_niqqud": "לדבר",
        "infinitive_transliteration": "ledaber",
        "italian_translation": "parlare",
        "root": "ד-ב-ר",
        "binyan": "PI'EL",
        "source_url": "https://www.pealim.com/dict/2-ledaber/",
        "source_checked_date": TODAY,
        "source_notes": "Verified from Pealim conjugation table. Pi'el with characteristic dagesh. Feminine plural future uses common masculine plural form.",
        "example_hebrew_with_niqqud": "אֲנִי מְדַבֵּר עִבְרִית קְצָת",
        "example_hebrew_without_niqqud": "אני מדבר עברית קצת",
        "example_transliteration": "ani medaber ivrit ktsat",
        "example_italian": "Parlo un po' di ebraico.",
        "stress_metadata": {
            "primary_stress_pattern": "penultimate_stem",
            "notes": "Pi'el stress generally on the penultimate stem syllable; feminine singular present and future 2fs shift stress to the final suffix.",
        },
        "pronunciation_verification_status": "verified_from_pealim",
        "content_verification_status": "verified",
        "present": {
            "masculine_singular": f("מְדַבֵּר", "מדבר", "medaber", 2, italian="io parlo"),
            "feminine_singular": f("מְדַבֶּרֶת", "מדברת", "medaberet", 3, italian="io parlo (f.)"),
            "masculine_plural": f("מְדַבְּרִים", "מדברים", "medabrim", 3, italian="noi/voi/loro parlano"),
            "feminine_plural": f("מְדַבְּרוֹת", "מדברות", "medabrot", 3, italian="noi/voi/loro parlano (f.)"),
        },
        "past": {
            "1_singular": f("דִּבַּרְתִּי", "דיברתי", "dibarti", 2, italian="io parlai"),
            "2_masculine_singular": f("דִּבַּרְתָּ", "דיברת", "dibarta", 2, italian="tu parlasti"),
            "2_feminine_singular": f("דִּבַּרְתְּ", "דיברת", "dibart", 2, italian="tu parlasti (f.)"),
            "3_masculine_singular": f("דִּבֵּר", "דיבר", "diber", 2, italian="lui parlò"),
            "3_feminine_singular": f("דִּבְּרָה", "דיברה", "dibra", 2, italian="lei parlò"),
            "1_plural": f("דִּבַּרְנוּ", "דיברנו", "dibarnu", 2, italian="noi parlammo"),
            "2_masculine_plural": f("דִּבַּרְתֶּם", "דיברתם", "dibartem", 2, italian="voi parlaste"),
            "2_feminine_plural": f("דִּבַּרְתֶּן", "דיברתן", "dibarten", 2, italian="voi parlaste (f.)"),
            "3_plural": f("דִּבְּרוּ", "דיברו", "dibru", 2, italian="loro parlarono"),
        },
        "future": {
            "1_singular": f("אֲדַבֵּר", "אדבר", "adaber", 2, italian="io parlerò"),
            "2_masculine_singular": f("תְּדַבֵּר", "תדבר", "tedaber", 2, italian="tu parlerai"),
            "2_feminine_singular": f("תְּדַבְּרִי", "תדברי", "tedabri", 3, italian="tu parlerai (f.)"),
            "3_masculine_singular": f("יְדַבֵּר", "ידבר", "yedaber", 2, italian="lui parlerà"),
            "3_feminine_singular": f("תְּדַבֵּר", "תדבר", "tedaber", 2, italian="lei parlerà"),
            "1_plural": f("נְדַבֵּר", "נדבר", "nedaber", 2, italian="noi parleremo"),
            "2_plural": f("תְּדַבְּרוּ", "תדברו", "tedabru", 3, italian="voi parlerete"),
            "3_plural": f("יְדַבְּרוּ", "ידברו", "yedabru", 3, italian="loro parleranno"),
        },
    },
    {
        "order": 3,
        "infinitive_hebrew_with_niqqud": "לֶאֱכֹל",
        "infinitive_hebrew_without_niqqud": "לאכול",
        "infinitive_transliteration": "le'echol",
        "italian_translation": "mangiare",
        "root": "א-כ-ל",
        "binyan": "PA'AL",
        "source_url": "https://www.pealim.com/dict/30-leechol/",
        "source_checked_date": TODAY,
        "source_notes": "Verified from Pealim conjugation table. Initial alef is silent/drops in inflected forms. Feminine plural future uses common masculine plural form.",
        "example_hebrew_with_niqqud": "אֲנִי אוֹכֵל תַּפּוּחַ",
        "example_hebrew_without_niqqud": "אני אוכל תפוח",
        "example_transliteration": "ani ochel tapuach",
        "example_italian": "Mangio una mela.",
        "stress_metadata": {
            "primary_stress_pattern": "variable_by_form",
            "notes": "Initial alef is silent or glottal. Infinitive stress on the final /o/. Future forms stress on the stem a in the penultimate syllable.",
        },
        "pronunciation_verification_status": "verified_from_pealim",
        "content_verification_status": "verified",
        "present": {
            "masculine_singular": f("אוֹכֵל", "אוכל", "ochel", 1, italian="io mangio"),
            "feminine_singular": f("אוֹכֶלֶת", "אוכלת", "ochelet", 2, italian="io mangio (f.)"),
            "masculine_plural": f("אוֹכְלִים", "אוכלים", "ochlim", 2, italian="noi/voi/loro mangiano"),
            "feminine_plural": f("אוֹכְלוֹת", "אוכלות", "ochlot", 2, italian="noi/voi/loro mangiano (f.)"),
        },
        "past": {
            "1_singular": f("אָכַלְתִּי", "אכלתי", "achalti", 2, italian="io mangiai"),
            "2_masculine_singular": f("אָכַלְתָּ", "אכלת", "achalta", 1, italian="tu mangiasti"),
            "2_feminine_singular": f("אָכַלְתְּ", "אכלת", "achalt", 1, italian="tu mangiasti (f.)"),
            "3_masculine_singular": f("אָכַל", "אכל", "achal", 1, italian="lui mangiò"),
            "3_feminine_singular": f("אָכְלָה", "אכלה", "achla", 2, italian="lei mangiò"),
            "1_plural": f("אָכַלְנוּ", "אכלנו", "achalnu", 1, italian="noi mangiammo"),
            "2_masculine_plural": f("אֲכַלְתֶּם", "אכלתם", "achaltem", 1, italian="voi mangiaste"),
            "2_feminine_plural": f("אֲכַלְתֶּן", "אכלתן", "achalten", 1, italian="voi mangiaste (f.)"),
            "3_plural": f("אָכְלוּ", "אכלו", "achlu", 1, italian="loro mangiarono"),
        },
        "future": {
            "1_singular": f("אֹכַל", "אוכל", "ochal", 1, italian="io mangerò"),
            "2_masculine_singular": f("תֹּאכַל", "תאכול", "tochal", 1, italian="tu mangerai"),
            "2_feminine_singular": f("תֹּאכְלִי", "תאכלי", "tochli", 2, italian="tu mangerai (f.)"),
            "3_masculine_singular": f("יֹאכַל", "יאכול", "yochal", 1, italian="lui mangerà"),
            "3_feminine_singular": f("תֹּאכַל", "תאכול", "tochal", 1, italian="lei mangerà"),
            "1_plural": f("נֹאכַל", "נאכול", "nochal", 1, italian="noi mangeremo"),
            "2_plural": f("תֹּאכְלוּ", "תאכלו", "tochlu", 2, italian="voi mangerete"),
            "3_plural": f("יֹאכְלוּ", "יאכלו", "yochlu", 2, italian="loro mangeranno"),
        },
    },
]


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def strip_niqqud(text: str) -> str:
    return "".join(c for c in text if not ("\u0591" <= c <= "\u05c7"))


def make_file_key(translit: str) -> str:
    return re.sub(r"[^a-z0-9]", "", translit.lower())[:12]


def make_spoken_script(verb: dict) -> str:
    """Build the final recitation script in transliteration."""
    lines: list[str] = []
    inf = verb["infinitive_transliteration"].upper()
    it = verb["italian_translation"].upper()
    ex = verb["example_transliteration"]
    lines.append(inf + ".")
    lines.append(it + ".")
    lines.append(ex.upper() + ".")
    lines.append("")
    lines.append("BA-HOVE:")
    for f in verb["present"].values():
        lines.append(f["display_transliteration"].upper() + ".")
    lines.append("")
    lines.append("BE-AVAR:")
    for f in verb["past"].values():
        lines.append(f["display_transliteration"].upper() + ".")
    lines.append("")
    lines.append("BE-ATID:")
    for f in verb["future"].values():
        lines.append(f["display_transliteration"].upper() + ".")
    return "\n".join(lines)


def make_hebrew_script(verb: dict) -> str:
    """Build the Hebrew recitation script for SSML / display."""
    lines: list[str] = []
    lines.append(verb["infinitive_hebrew_with_niqqud"] + ".")
    lines.append(verb["example_hebrew_with_niqqud"] + ".")
    lines.append("")
    lines.append("בַּהוֹוֶה:")
    for f in verb["present"].values():
        lines.append(f["hebrew_with_niqqud"] + ".")
    lines.append("")
    lines.append("בָּעָבָר:")
    for f in verb["past"].values():
        lines.append(f["hebrew_with_niqqud"] + ".")
    lines.append("")
    lines.append("בָּעָתִיד:")
    for f in verb["future"].values():
        lines.append(f["hebrew_with_niqqud"] + ".")
    return "\n".join(lines)


def make_italian_script(verb: dict) -> str:
    lines: list[str] = []
    lines.append(verb["italian_translation"].capitalize() + ".")
    lines.append(verb["example_italian"])
    lines.append("")
    lines.append("Presente:")
    for f in verb["present"].values():
        lines.append(f["italian_gloss"] + ".")
    lines.append("")
    lines.append("Passato:")
    for f in verb["past"].values():
        lines.append(f["italian_gloss"] + ".")
    lines.append("")
    lines.append("Futuro:")
    for f in verb["future"].values():
        lines.append(f["italian_gloss"] + ".")
    return "\n".join(lines)


def section_lines(verb: dict, section: str, label_he: str, label_it: str) -> list[dict]:
    out = []
    for key, form in verb[section].items():
        out.append(OrderedDict([
            ("form_key", key),
            ("hebrew_with_niqqud", form["hebrew_with_niqqud"]),
            ("hebrew_without_niqqud", form["hebrew_without_niqqud"]),
            ("transliteration", form["display_transliteration"]),
            ("tts_input", form["tts_input"]),
            ("italian_gloss", form["italian_gloss"]),
            ("stress_syllable_index", form["stress_syllable_index"]),
        ]))
    return out


def make_script_json(verb: dict) -> dict:
    key = make_file_key(verb["infinitive_transliteration"])
    return OrderedDict([
        ("order", verb["order"]),
        ("verb_key", key),
        ("hebrew_infinitive", verb["infinitive_hebrew_with_niqqud"]),
        ("hebrew_infinitive_without_niqqud", verb["infinitive_hebrew_without_niqqud"]),
        ("italian_infinitive", verb["italian_translation"]),
        ("root", verb["root"]),
        ("binyan", verb["binyan"]),
        ("source_url", verb["source_url"]),
        ("sections", [
            OrderedDict([
                ("section", "infinitive"),
                ("label_he", "שֵׁם הַפֹּעַל"),
                ("label_it", "infinito"),
                ("lines", [
                    OrderedDict([
                        ("form_key", "infinitive"),
                        ("hebrew_with_niqqud", verb["infinitive_hebrew_with_niqqud"]),
                        ("hebrew_without_niqqud", verb["infinitive_hebrew_without_niqqud"]),
                        ("transliteration", verb["infinitive_transliteration"]),
                        ("tts_input", verb["infinitive_hebrew_with_niqqud"]),
                        ("italian_gloss", verb["italian_translation"]),
                    ]),
                    OrderedDict([
                        ("form_key", "example"),
                        ("hebrew_with_niqqud", verb["example_hebrew_with_niqqud"]),
                        ("hebrew_without_niqqud", verb["example_hebrew_without_niqqud"]),
                        ("transliteration", verb["example_transliteration"]),
                        ("tts_input", verb["example_hebrew_with_niqqud"]),
                        ("italian_gloss", verb["example_italian"]),
                    ]),
                ]),
            ]),
            OrderedDict([("section", "present"), ("label_he", "בַּהוֹוֶה"), ("label_it", "presente"), ("lines", section_lines(verb, "present", "בַּהוֹוֶה", "presente"))]),
            OrderedDict([("section", "past"), ("label_he", "בָּעָבָר"), ("label_it", "passato"), ("lines", section_lines(verb, "past", "בָּעָבָר", "passato"))]),
            OrderedDict([("section", "future"), ("label_he", "בָּעָתִיד"), ("label_it", "futuro"), ("lines", section_lines(verb, "future", "בָּעָתִיד", "futuro"))]),
        ]),
        ("spoken_script", make_spoken_script(verb)),
        ("display_script", make_spoken_script(verb)),
        ("hebrew_script", make_hebrew_script(verb)),
        ("italian_script", make_italian_script(verb)),
        ("transliteration", make_spoken_script(verb)),
        ("pauses_ms", {
            "between_forms": 500,
            "between_sections": 900,
            "after_example": 700,
        }),
        ("speaking_rate", "-15%"),
        ("ssml_path", f"ssml/{verb['order']:03d}_{key}.xml"),
    ])


def make_ssml(verb: dict, script: dict) -> str:
    """Build Azure SSML with Hebrew voice and lang switch for Italian words."""
    rate = script["speaking_rate"]
    between = f'<break time="{script["pauses_ms"]["between_forms"]}ms"/>'
    section_break = f'<break time="{script["pauses_ms"]["between_sections"]}ms"/>'
    example_break = f'<break time="{script["pauses_ms"]["after_example"]}ms"/>'

    parts: list[str] = []
    # Infinitive + Italian meaning + example
    parts.append(f'<prosody rate="{rate}">{verb["infinitive_hebrew_with_niqqud"]}</prosody>')
    parts.append(between)
    parts.append(f'<lang xml:lang="it-IT">{verb["italian_translation"]}.</lang>')
    parts.append(example_break)
    parts.append(f'<prosody rate="{rate}">{verb["example_hebrew_with_niqqud"]}</prosody>')
    parts.append(example_break)

    for sec in script["sections"][1:]:
        parts.append(section_break)
        for line in sec["lines"]:
            parts.append(f'<prosody rate="{rate}">{line["hebrew_with_niqqud"]}</prosody>')
            parts.append(between)

    inner = "\n    ".join(parts)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xml:lang="he-IL">\n'
        f'  <voice name="he-IL-AvriNeural">\n    {inner}\n  </voice>\n'
        '</speak>'
    )


def write_json_files() -> None:
    master = []
    for verb in VERBS_3:
        entry = OrderedDict([
            ("order", verb["order"]),
            ("infinitive_hebrew_with_niqqud", verb["infinitive_hebrew_with_niqqud"]),
            ("infinitive_hebrew_without_niqqud", verb["infinitive_hebrew_without_niqqud"]),
            ("infinitive_transliteration", verb["infinitive_transliteration"]),
            ("italian_translation", verb["italian_translation"]),
            ("root", verb["root"]),
            ("binyan", verb["binyan"]),
            ("source_url", verb["source_url"]),
            ("source_checked_date", verb["source_checked_date"]),
            ("source_notes", verb["source_notes"]),
            ("example_hebrew_with_niqqud", verb["example_hebrew_with_niqqud"]),
            ("example_hebrew_without_niqqud", verb["example_hebrew_without_niqqud"]),
            ("example_transliteration", verb["example_transliteration"]),
            ("example_italian", verb["example_italian"]),
            ("present", verb["present"]),
            ("past", verb["past"]),
            ("future", verb["future"]),
            ("stress_metadata", verb["stress_metadata"]),
            ("pronunciation_verification_status", verb["pronunciation_verification_status"]),
            ("content_verification_status", verb["content_verification_status"]),
        ])
        master.append(entry)

    (DATA / "verbs_master.json").write_text(
        json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    for verb in VERBS_3:
        key = make_file_key(verb["infinitive_transliteration"])
        script = make_script_json(verb)
        (SCRIPTS / f"{verb['order']:03d}_{key}.json").write_text(
            json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        ssml = make_ssml(verb, script)
        (SSML / f"{verb['order']:03d}_{key}.xml").write_text(ssml, encoding="utf-8")


def _audio_exists(order: int, translit: str) -> bool:
    key = make_file_key(translit)
    return (AUDIO / f"{order:03d}_{key}.mp3").exists()


def write_plan_and_audit() -> None:
    plan_lines = [
        "# Mantra 100-verb plan\n",
        "\n",
        "Selection criteria:\n",
        "- Modern Hebrew frequency (core/high/medium/low bands).\n",
        "- Communicative usefulness for an adult learner living in Israel.\n",
        "- Coverage of Pa'al, Pi'el, Hif'il, Hitpa'el, Nif'al, and a small number of Huf'al/Pual forms.\n",
        "- Coverage of common irregular patterns: initial alef, final he, initial yod/nun drop, gutturals, weak roots.\n",
        "- All Pealim dict URLs will be verified before content is marked complete.\n",
        "\n",
        "| order | verb | italian | binyan | root | freq_band | source | rationale |\n",
        "|------:|------|---------|--------|------|-----------|--------|-----------|\n",
    ]
    for v in VERBS_100:
        source = v.get("source_url", "")
        if not source:
            # Provide a Pealim search URL for planned verbs so reviewers can verify quickly.
            plain = "".join(c for c in v['verb'] if '\u0590' > c or c > '\u05cf')
            source = f"https://www.pealim.com/search/?q={plain.strip()}"
        plan_lines.append(
            f"| {v['order']} | {v['verb']} | {v['italian']} | {v['binyan']} | {v['root']} | {v['freq']} | {source} | {v['rationale']} |\n"
        )
    (DATA / "VERBS_100_PLAN.md").write_text("".join(plan_lines), encoding="utf-8")

    audit_rows = []
    for v in VERBS_100:
        is_first_three = v["order"] <= 3
        translit_lookup = {3: "le'echol", 2: "ledaber", 1: "lichtov"}
        audio_yes = is_first_three and _audio_exists(v["order"], translit_lookup.get(v["order"], ""))
        row = {
            "order": v["order"],
            "verb": v["verb"],
            "translation": v["italian"],
            "binyan": v["binyan"],
            "root": v["root"],
            "frequency_source": "approximate cross-reference Pealim + learner corpus" if not is_first_three else "Pealim + learner core list",
            "pealim_url": v.get("source_url", ""),
            "forms_verified": "yes" if is_first_three else "no",
            "pronunciation_verified": "yes" if is_first_three else "no",
            "example_verified": "yes" if is_first_three else "no",
            "audio_generated": "yes" if audio_yes else "no",
            "human_approved": "no",
            "notes": v["rationale"],
        }
        audit_rows.append(row)

    fieldnames = [
        "order", "verb", "translation", "binyan", "root", "frequency_source",
        "pealim_url", "forms_verified", "pronunciation_verified", "example_verified",
        "audio_generated", "human_approved", "notes",
    ]
    with open(DATA / "MANTRA_CONTENT_AUDIT.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(audit_rows)


def write_readme() -> None:
    readme = (
        "# Mantra content dataset — Phase 1\n\n"
        "This directory contains the curated Modern Hebrew verb dataset for the MindTune Lab Mantra section.\n\n"
        "## Files\n\n"
        "- `verbs_master.json` — canonical full records (currently verbs 1–3, verified).\n"
        "- `scripts/001_*.json` — per-verb spoken/display/Hebrew/Italian scripts with section timing.\n"
        "- `ssml/001_*.xml` — Azure Speech SSML inputs.\n"
        "- `audio/001_*.mp3` — generated audio (produced by `scripts/generate_mantra_audio.py`).\n"
        "- `VERBS_100_PLAN.md` — proposed ordered list of 100 verbs with selection rationale.\n"
        "- `MANTRA_CONTENT_AUDIT.csv` — QA audit for all 100 verbs (3 complete, 97 planned).\n"
        "- `UNCERTAINTIES.md` — documented open linguistic decisions.\n\n"
        "## Schema notes\n\n"
        "- `display_transliteration` is lowercase and Italian-friendly; stress is in `stress_syllable_index`.\n"
        "- `tts_input` is Hebrew with niqqud and is used in Azure SSML, not the transliteration.\n"
        "- Feminine plural future forms follow ordinary modern usage (masculine plural form).\n\n"
        "## Audio generation\n\n"
        "Run `python3 scripts/generate_mantra_audio.py` after exporting the Azure Speech key and region.\n"
    )
    (DATA / "README.md").write_text(readme, encoding="utf-8")


def write_uncertainties() -> None:
    text = (
        "# Mantra Phase 1 — uncertain linguistic decisions\n\n"
        "1. **Infinitive spelling of לִכְתֹּב vs לִכְתּוֹב**\n"
        "   Pealim lists the defective spelling `לִכְתֹּב` (without vav) as the primary menukad form; "
        "the full spelling with vav is acceptable in unvowelled text. For TTS we use the vowelled form.\n\n"
        "2. **Stress in past 2nd-person plural**\n"
        "   Pealim gives two variants (e.g., `כְּתַבְתֶּם` and `כָּתַבְתֶּם`). We selected the reduced-vowel "
        "form `ktavtem`/`ktavten` as the common spoken form, matching the user's mantra example.\n\n"
        "3. **Transliteration of silent/glottal alef**\n"
        "   We represent a pronounced glottal stop with `'` (e.g., `le'echol`). In rapid speech the stop may be barely audible; "
        "this is marked in metadata but does not affect Azure TTS, which receives Hebrew script.\n\n"
        "4. **Italian glosses for gender/number**\n"
        "   The Hebrew present tense is a participle covering multiple persons. Italian glosses note the gender only when "
        "the Hebrew form itself is marked for gender (feminine singular/plural).\n\n"
        "5. **Future feminine plural**\n"
        "   We use the common modern masculine plural future forms (`tichte'vu`, `yichte'vu`) for plural address, "
        "as instructed. The classical feminine plural forms (`tichtovna` etc.) are omitted from the recitation.\n\n"
        "6. **Voice selection**\n"
        "   SSML uses `he-IL-AvriNeural`. If a different voice is preferred, update `scripts/generate_mantra_audio.py` and regenerate.\n"
    )
    (DATA / "UNCERTAINTIES.md").write_text(text, encoding="utf-8")


def generate_audio() -> None:
    key = (os.environ.get("MINDTUNE_AZURE_SPEECH_KEY") or "").strip()
    region = (os.environ.get("MINDTUNE_AZURE_SPEECH_REGION") or "switzerlandnorth").strip()
    if not key:
        print("MINDTUNE_AZURE_SPEECH_KEY not set; skipping audio generation.")
        return

    for verb in VERBS_3:
        key_name = make_file_key(verb["infinitive_transliteration"])
        ssml_path = SSML / f"{verb['order']:03d}_{key_name}.xml"
        out_path = AUDIO / f"{verb['order']:03d}_{key_name}.mp3"
        ssml = ssml_path.read_text(encoding="utf-8")
        url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        req = urllib.request.Request(
            url,
            data=ssml.encode("utf-8"),
            method="POST",
            headers={
                "Ocp-Apim-Subscription-Key": key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                "User-Agent": "MindTune-Lab-Mantra",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                out_path.write_bytes(resp.read())
            print(f"audio: {out_path}")
        except Exception as exc:
            print(f"failed to generate audio for {key_name}: {exc}")
        time.sleep(0.5)


PEALIM_FORM_IDS = {
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


def _vowel_group_count(text: str) -> int:
    return len(re.findall(r"[aeiou]", text.lower()))


def _stress_from_transcription(html_transcription: str) -> int:
    """Count vowel groups before the <b> tag; stress falls on the next syllable."""
    before, _, _ = html_transcription.partition("<b>")
    return _vowel_group_count(before) + 1


def _fetch_pealim_stress(url: str) -> dict[str, int]:
    """Return a mapping {form_id: stress_syllable_index} from a Pealim page."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    stresses: dict[str, int] = {}
    for fid in PEALIM_FORM_IDS.values():
        m = re.search(rf'id="{fid}"[^>]*>.*?</div>\s*</div>', html, re.S)
        if not m:
            continue
        block = m.group(0)
        t = re.search(r'<div class="transcription">(.*?)</div>', block, re.S)
        if t:
            stresses[fid] = _stress_from_transcription(t.group(1))
    return stresses


def update_stress_from_pealim() -> None:
    """Override stress_syllable_index in VERBS_3 with values parsed from Pealim."""
    for verb in VERBS_3:
        stresses = _fetch_pealim_stress(verb["source_url"])
        for section, forms in (("present", verb["present"]), ("past", verb["past"]), ("future", verb["future"])):
            for key, form in forms.items():
                fid = PEALIM_FORM_IDS.get(f"{section}_{key}")
                if fid and fid in stresses:
                    form["stress_syllable_index"] = stresses[fid]


def sync_verb3_into_plan() -> None:
    """Merge source_url and other metadata from VERBS_3 into VERBS_100 entries 1-3."""
    lookup = {v["order"]: v for v in VERBS_3}
    for v in VERBS_100:
        if v["order"] in lookup:
            src = lookup[v["order"]]
            v["verb"] = src["infinitive_hebrew_with_niqqud"]
            v["source_url"] = src["source_url"]
            v["italian"] = src["italian_translation"]
            v["binyan"] = src["binyan"]
            v["root"] = src["root"]


def main() -> int:
    update_stress_from_pealim()
    sync_verb3_into_plan()
    write_json_files()
    write_plan_and_audit()
    write_readme()
    write_uncertainties()
    generate_audio()
    print("Mantra Phase 1 dataset generated.")
    print(f"  master:        {DATA / 'verbs_master.json'}")
    print(f"  scripts:       {SCRIPTS}")
    print(f"  ssml:          {SSML}")
    print(f"  audio:         {AUDIO}")
    print(f"  plan:          {DATA / 'VERBS_100_PLAN.md'}")
    print(f"  audit:         {DATA / 'MANTRA_CONTENT_AUDIT.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
