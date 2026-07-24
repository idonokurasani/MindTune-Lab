#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "mindtune_console" / "data"
CITIZEN = DATA / "citizen_cafe_all_courses" / "CITIZEN_CAFE_ALL_COURSES_CANONICAL_MODEL_DRAFT_v1.1.json"
OUT = DATA / "hebrew_enrichment" / "streetwise_hebrew"

HEBREW_RE = re.compile(r"[\u0590-\u05ff]")
HEBREW_MARKS_RE = re.compile(r"[\u0591-\u05bd\u05bf-\u05c7]")
SPACE_RE = re.compile(r"\s+")
MAX_EXCERPT_CHARS = 180
MAX_EXAMPLES_PER_PAGE = 80


@dataclass
class SourceDocument:
    source_id: str
    source_label: str
    source_type: str
    declared_source_type: str
    url: str
    file_path: str
    title: str
    description: str
    audio_urls: list[str]
    text: str
    retrieved_at: str
    content_sha256: str
    published_at: str = ""
    episode_guid: str = ""
    source_parent_url: str = ""
    lexical_entries: list[dict[str, str]] = field(default_factory=list)


class StreetwiseHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.audio_urls: list[str] = []
        self.meta_description = ""
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "description" or prop == "og:description":
                self.meta_description = clean_space(attrs_dict.get("content", ""))
        if tag in {"audio", "source", "a"}:
            href = attrs_dict.get("src") or attrs_dict.get("href") or ""
            if href and re.search(r"\.(mp3|m4a|wav|aac)(?:$|\?)", href, re.I):
                self.audio_urls.append(href)
        if tag in {"p", "div", "li", "br", "h1", "h2", "h3", "h4"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._skip_depth and tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False
        if tag in {"p", "div", "li", "h1", "h2", "h3", "h4"}:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self.title_parts.append(data)
        self.text_parts.append(data)

    @property
    def title(self) -> str:
        return clean_space(" ".join(self.title_parts))

    @property
    def text(self) -> str:
        lines = [clean_space(line) for line in "\n".join(self.text_parts).splitlines()]
        return "\n".join(line for line in lines if line)


def clean_space(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = text.replace("\u200e", "").replace("\u200f", "").replace("\ufeff", "")
    return SPACE_RE.sub(" ", text).strip()


def strip_niqqud(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = HEBREW_MARKS_RE.sub("", text)
    text = "".join(ch for ch in text if not (unicodedata.combining(ch) and "\u0590" <= ch <= "\u05ff"))
    return unicodedata.normalize("NFC", text)


def normalize_hebrew(value: Any) -> str:
    text = strip_niqqud(value)
    text = re.sub(r"[^\u0590-\u05ff]+", " ", text)
    return clean_space(text)


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "\u241f".join(str(part or "") for part in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]}"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_canonical_items() -> list[dict[str, Any]]:
    payload = read_json(CITIZEN)
    return [
        item
        for item in payload.get("items", [])
        if item.get("status") == "candidate_ready" and item.get("hebrew")
    ]


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "MindTuneLab-Streetwise-Enrichment/0.1 (+local research import; metadata only)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def parse_source_type(url: str, title: str, file_path: str, declared_source_type: str = "") -> str:
    declared = clean_space(declared_source_type)
    if declared:
        return declared
    joined = f"{url} {title} {file_path}".lower()
    if "quiz" in joined:
        return "quiz"
    if "snippet" in joined:
        return "snippet"
    if "tlv1.fm" in joined or "episode" in joined or "podcast" in joined:
        return "episode"
    return "page"


def parse_html_document(
    payload: bytes,
    url: str = "",
    file_path: str = "",
    retrieved_at: str = "",
    source_label: str = "",
    declared_source_type: str = "",
) -> SourceDocument:
    parser = StreetwiseHTMLParser()
    text = payload.decode("utf-8", errors="replace")
    parser.feed(text)
    title = parser.title or clean_space(Path(file_path).stem if file_path else urlparse(url).path.rsplit("/", 1)[-1])
    source_type = parse_source_type(url, title, file_path, declared_source_type)
    source_id = stable_id("streetwise_src", source_label, url or file_path, sha256_bytes(payload))
    return SourceDocument(
        source_id=source_id,
        source_label=clean_space(source_label) or title,
        source_type=source_type,
        declared_source_type=clean_space(declared_source_type),
        url=url,
        file_path=file_path,
        title=title,
        description=parser.meta_description,
        audio_urls=sorted(set(parser.audio_urls)),
        text=parser.text,
        retrieved_at=retrieved_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        content_sha256=sha256_bytes(payload),
    )


def parse_published_at(value: Any) -> str:
    raw = clean_space(value)
    if not raw:
        return ""
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, OverflowError):
        return raw


def xml_text(node: ET.Element, local_name: str) -> str:
    for child in node.iter():
        if child.tag.rsplit("}", 1)[-1] == local_name:
            return clean_space(child.text)
    return ""


def parse_rss_documents(
    payload: bytes,
    url: str = "",
    file_path: str = "",
    retrieved_at: str = "",
    source_label: str = "",
) -> list[SourceDocument]:
    root = ET.fromstring(payload)
    channel = next((node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "channel"), root)
    feed_title = xml_text(channel, "title") or clean_space(source_label) or "Streetwise Hebrew"
    generated_at = retrieved_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    documents: list[SourceDocument] = []
    for item in (node for node in channel if node.tag.rsplit("}", 1)[-1] == "item"):
        title = xml_text(item, "title")
        link = xml_text(item, "link")
        guid = xml_text(item, "guid")
        description_html = xml_text(item, "encoded") or xml_text(item, "description")
        description_payload = description_html.encode("utf-8")
        parsed_description = parse_html_document(
            description_payload,
            url=link or url,
            retrieved_at=generated_at,
            source_label=title,
            declared_source_type="episode",
        )
        audio_urls = list(parsed_description.audio_urls)
        for child in item:
            if child.tag.rsplit("}", 1)[-1] == "enclosure":
                enclosure_url = clean_space(child.attrib.get("url"))
                if enclosure_url:
                    audio_urls.append(enclosure_url)
        identity = guid or link or title
        source_id = stable_id("streetwise_episode", identity)
        documents.append(
            SourceDocument(
                source_id=source_id,
                source_label=f"{feed_title}: {title}" if title else feed_title,
                source_type="episode",
                declared_source_type="podcast_rss",
                url=link or url,
                file_path=file_path,
                title=title,
                description=parsed_description.description or clean_space(parsed_description.text)[:MAX_EXCERPT_CHARS],
                audio_urls=sorted(set(audio_urls)),
                text=parsed_description.text,
                retrieved_at=generated_at,
                content_sha256=sha256_bytes(description_payload),
                published_at=parse_published_at(xml_text(item, "pubDate")),
                episode_guid=guid,
                source_parent_url=url,
            )
        )
    return documents


def parse_verified_snapshot(
    payload: bytes,
    file_path: str,
    retrieved_at: str = "",
) -> list[SourceDocument]:
    data = json.loads(payload.decode("utf-8-sig"))
    if not str(data.get("schema", "")).startswith("mindtune.streetwise_verified_episode_seed"):
        raise ValueError("Unsupported Streetwise JSON snapshot schema")
    generated_at = retrieved_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    parent_url = clean_space(data.get("source_feed_url"))
    documents: list[SourceDocument] = []
    for episode in data.get("episodes", []):
        title = clean_space(episode.get("title"))
        audio_url = clean_space(episode.get("audio_url"))
        episode_url = clean_space(episode.get("episode_url")) or parent_url
        guid = clean_space(episode.get("guid")) or audio_url or episode_url
        lines = [clean_space(episode.get("summary"))]
        lexical_entries: list[dict[str, str]] = []
        for entry in episode.get("lexical_entries", []):
            hebrew = clean_space(entry.get("hebrew"))
            english = clean_space(entry.get("english_gloss"))
            transliteration = clean_space(entry.get("transliteration"))
            if hebrew:
                lines.append(" - ".join(part for part in (transliteration, english, hebrew) if part))
                lexical_entries.append(
                    {
                        "hebrew": hebrew,
                        "hebrew_normalized": normalize_hebrew(hebrew),
                        "english_gloss": english,
                        "transliteration": transliteration,
                    }
                )
        text = "\n".join(line for line in lines if line)
        encoded = text.encode("utf-8")
        documents.append(
            SourceDocument(
                source_id=stable_id("streetwise_episode", guid),
                source_label=f"Streetwise Hebrew: {title}",
                source_type="episode",
                declared_source_type="verified_public_snapshot",
                url=episode_url,
                file_path=file_path,
                title=title,
                description=clean_space(episode.get("summary"))[:MAX_EXCERPT_CHARS],
                audio_urls=[audio_url] if audio_url else [],
                text=text,
                retrieved_at=generated_at,
                content_sha256=sha256_bytes(encoded),
                published_at=clean_space(episode.get("published_at")),
                episode_guid=guid,
                source_parent_url=parent_url,
                lexical_entries=lexical_entries,
            )
        )
    return documents


def parse_input_documents(
    payload: bytes,
    url: str = "",
    file_path: str = "",
    retrieved_at: str = "",
    source_label: str = "",
    declared_source_type: str = "",
) -> list[SourceDocument]:
    suffix = Path(file_path).suffix.lower()
    content = payload.lstrip()
    if suffix == ".json" or content.startswith(b"{"):
        return parse_verified_snapshot(payload, file_path=file_path, retrieved_at=retrieved_at)
    if declared_source_type in {"podcast_rss", "rss"} or suffix in {".rss", ".xml"} or content.startswith(b"<?xml"):
        return parse_rss_documents(
            payload,
            url=url,
            file_path=file_path,
            retrieved_at=retrieved_at,
            source_label=source_label,
        )
    return [
        parse_html_document(
            payload,
            url=url,
            file_path=file_path,
            retrieved_at=retrieved_at,
            source_label=source_label,
            declared_source_type=declared_source_type,
        )
    ]


def excerpt_around(text: str, needle: str) -> str:
    idx = text.find(needle)
    if idx < 0:
        return ""
    start = max(0, idx - MAX_EXCERPT_CHARS // 2)
    end = min(len(text), idx + len(needle) + MAX_EXCERPT_CHARS // 2)
    excerpt = clean_space(text[start:end])
    if start > 0:
        excerpt = "..." + excerpt
    if end < len(text):
        excerpt += "..."
    return excerpt[: MAX_EXCERPT_CHARS + 6]


def contains_hebrew_phrase(normalized_text: str, normalized_phrase: str) -> bool:
    phrase = clean_space(normalized_phrase)
    if not phrase:
        return False
    pattern = r"(?:^|\s)" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?:\s|$)"
    return re.search(pattern, normalized_text) is not None


def hebrew_line_snippets(text: str) -> list[str]:
    snippets: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        line = clean_space(line)
        if not HEBREW_RE.search(line):
            continue
        normalized = normalize_hebrew(line)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        snippets.append(line[:MAX_EXCERPT_CHARS])
        if len(snippets) >= MAX_EXAMPLES_PER_PAGE:
            break
    return snippets


def build_matches(doc: SourceDocument, canonical_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    normalized_text = normalize_hebrew(doc.text)
    raw_snippets = hebrew_line_snippets(doc.text)
    normalized_snippets = [(raw, normalize_hebrew(raw)) for raw in raw_snippets]
    matches: list[dict[str, Any]] = []
    enrichment_records: list[dict[str, Any]] = []
    for item in canonical_items:
        hebrew = normalize_hebrew(item.get("hebrew"))
        if not hebrew or len(hebrew) < 2:
            continue
        exact_snippet = next((raw for raw, normalized in normalized_snippets if normalized == hebrew), "")
        phrase_match = (
            not exact_snippet
            and len(hebrew.split()) >= 2
            and len(hebrew.replace(" ", "")) >= 5
            and contains_hebrew_phrase(normalized_text, hebrew)
        )
        if not exact_snippet and not phrase_match:
            continue
        excerpt = clean_space(exact_snippet) if exact_snippet else excerpt_around(normalized_text, hebrew) or hebrew
        match_type = "exact_lexical_entry" if exact_snippet else "normalized_hebrew_phrase"
        confidence = "high" if exact_snippet else "medium"
        match_id = stable_id("streetwise_match", doc.source_id, item.get("canonical_item_id"), hebrew)
        matches.append(
            {
                "match_id": match_id,
                "source_id": doc.source_id,
                "canonical_item_id": item.get("canonical_item_id"),
                "deck": item.get("deck"),
                "hebrew": item.get("hebrew"),
                "italian": item.get("italian"),
                "match_type": match_type,
                "match_confidence": confidence,
                "context_excerpt": excerpt,
                "review_status": "draft_unverified",
            }
        )
        enrichment_records.append(
            {
                "enrichment_id": stable_id("streetwise_enrich", match_id),
                "canonical_item_id": item.get("canonical_item_id"),
                "source": "streetwise_hebrew",
                "source_ref": {
                    "source_id": doc.source_id,
                    "source_label": doc.source_label,
                    "source_type": doc.source_type,
                    "title": doc.title,
                    "url": doc.url,
                    "file_path": doc.file_path,
                    "retrieved_at": doc.retrieved_at,
                    "content_sha256": doc.content_sha256,
                },
                "usage_examples": [
                    {
                        "hebrew_excerpt": excerpt,
                        "italian_gloss": "",
                        "register": "unknown",
                        "confidence": confidence,
                    }
                ],
                "audio_refs": doc.audio_urls[:5],
                "notes": [
                    "Metadata/enrichment candidate only; not a canonical Citizen Cafe translation.",
                    "Excerpt intentionally short to avoid transcript reproduction.",
                ],
                "review_status": "draft_unverified",
            }
        )
    if not matches and raw_snippets:
        matches.append(
            {
                "match_id": stable_id("streetwise_unmatched", doc.source_id),
                "source_id": doc.source_id,
                "canonical_item_id": "",
                "deck": "",
                "hebrew": "",
                "italian": "",
                "match_type": "unmatched_hebrew_page",
                "match_confidence": "low",
                "context_excerpt": raw_snippets[0],
                "review_status": "source_only",
            }
        )
    return matches, enrichment_records


def build_lexical_evidence(doc: SourceDocument) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    entries = doc.lexical_entries or [
        {
            "hebrew": snippet,
            "hebrew_normalized": normalize_hebrew(snippet),
            "english_gloss": "",
            "transliteration": "",
        }
        for snippet in hebrew_line_snippets(doc.text)
    ]
    seen: set[str] = set()
    for entry in entries:
        normalized = normalize_hebrew(entry.get("hebrew_normalized") or entry.get("hebrew"))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        rows.append(
            {
                "evidence_id": stable_id("streetwise_lex", doc.source_id, normalized),
                "source_id": doc.source_id,
                "source": "streetwise_hebrew",
                "episode_title": doc.title,
                "published_at": doc.published_at,
                "episode_url": doc.url,
                "audio_urls": doc.audio_urls[:3],
                "hebrew": clean_space(entry.get("hebrew")),
                "hebrew_normalized": normalized,
                "english_gloss": clean_space(entry.get("english_gloss")),
                "transliteration": clean_space(entry.get("transliteration")),
                "evidence_role": "spoken_usage_enrichment",
                "review_status": "draft_unverified",
            }
        )
    return rows


def source_rows_from_list(path: Path, allowed_statuses: set[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            row = {str(key or "").strip(): clean_space(value) for key, value in raw.items()}
            status = row.get("import_status", "")
            if allowed_statuses and status not in allowed_statuses:
                continue
            if not row.get("url") and not row.get("file_path"):
                continue
            rows.append(row)
    return rows


def collect_inputs(args: argparse.Namespace) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    allowed_statuses = set(args.include_status or [])
    for list_name in args.source_list or []:
        list_path = Path(list_name).expanduser().resolve()
        for row in source_rows_from_list(list_path, allowed_statuses):
            if row.get("url"):
                collected.append(
                    {
                        "payload": None,
                        "url": row["url"],
                        "file_path": "",
                        "source_label": row.get("source_label", ""),
                        "declared_source_type": row.get("source_type", ""),
                        "source_list": str(list_path),
                        "import_status": row.get("import_status", ""),
                        "notes": row.get("notes", ""),
                    }
                )
            elif row.get("file_path"):
                path = Path(row["file_path"]).expanduser().resolve()
                collected.append(
                    {
                        "payload": path.read_bytes(),
                        "url": "",
                        "file_path": str(path),
                        "source_label": row.get("source_label", ""),
                        "declared_source_type": row.get("source_type", ""),
                        "source_list": str(list_path),
                        "import_status": row.get("import_status", ""),
                        "notes": row.get("notes", ""),
                    }
                )
    for url in args.url or []:
        collected.append(
            {
                "payload": None,
                "url": url,
                "file_path": "",
                "source_label": "",
                "declared_source_type": "",
                "source_list": "",
                "import_status": "direct",
                "notes": "",
            }
        )
    for file_name in args.file or []:
        path = Path(file_name).expanduser().resolve()
        collected.append(
            {
                "payload": path.read_bytes(),
                "url": "",
                "file_path": str(path),
                "source_label": "",
                "declared_source_type": "",
                "source_list": "",
                "import_status": "direct",
                "notes": "",
            }
        )
    for dir_name in args.dir or []:
        root = Path(dir_name).expanduser().resolve()
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".html", ".htm", ".xml", ".rss", ".json"}:
                collected.append(
                    {
                        "payload": path.read_bytes(),
                        "url": "",
                        "file_path": str(path),
                        "source_label": "",
                        "declared_source_type": "",
                        "source_list": "",
                        "import_status": "direct",
                        "notes": "",
                    }
                )
    return collected


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Streetwise Hebrew metadata/enrichment candidates.")
    parser.add_argument("--url", action="append", help="Streetwise/TLV1 page URL to fetch. Use sparingly; no crawl.")
    parser.add_argument("--file", action="append", help="Saved HTML file to import.")
    parser.add_argument("--dir", action="append", help="Directory containing saved HTML files.")
    parser.add_argument("--source-list", action="append", help="CSV source list with url/file_path and import_status.")
    parser.add_argument(
        "--include-status",
        action="append",
        default=None,
        help="Import source-list rows with this status. Default: queued and selected.",
    )
    parser.add_argument("--max-pages", type=int, default=10, help="Safety limit for one import run.")
    parser.add_argument("--dry-run", action="store_true", help="List selected sources without fetching URLs or writing outputs.")
    parser.add_argument("--out", default=str(OUT), help="Output directory.")
    args = parser.parse_args()
    if args.include_status is None:
        args.include_status = ["queued", "selected"]

    out_dir = Path(args.out).expanduser().resolve()
    canonical_items = load_canonical_items()
    inputs = collect_inputs(args)
    if not inputs:
        raise SystemExit("No input. Use --url, --file, --dir, or --source-list with queued/selected rows.")
    if len(inputs) > args.max_pages:
        raise SystemExit(f"Refusing to import {len(inputs)} sources; raise --max-pages explicitly if intentional.")
    if args.dry_run:
        for index, item in enumerate(inputs, start=1):
            print(
                f"{index}. {item.get('source_label') or item.get('url') or item.get('file_path')} "
                f"[type={item.get('declared_source_type') or 'auto'} status={item.get('import_status')}]"
            )
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sources: list[dict[str, Any]] = []
    all_matches: list[dict[str, Any]] = []
    all_enrichment: list[dict[str, Any]] = []
    all_lexical_evidence: list[dict[str, Any]] = []

    for item in inputs:
        payload = item["payload"] if item.get("payload") is not None else fetch_url(item["url"])
        documents = parse_input_documents(
            payload,
            url=item.get("url", ""),
            file_path=item.get("file_path", ""),
            retrieved_at=generated_at,
            source_label=item.get("source_label", ""),
            declared_source_type=item.get("declared_source_type", ""),
        )
        for doc in documents:
            matches, enrichment = build_matches(doc, canonical_items)
            sources.append(
                {
                    "source_id": doc.source_id,
                    "source": "streetwise_hebrew",
                    "source_label": doc.source_label,
                    "source_type": doc.source_type,
                    "declared_source_type": doc.declared_source_type,
                    "title": doc.title,
                    "description": doc.description[:MAX_EXCERPT_CHARS],
                    "url": doc.url,
                    "source_parent_url": doc.source_parent_url,
                    "file_path": doc.file_path,
                    "source_list": item.get("source_list", ""),
                    "import_status": item.get("import_status", ""),
                    "notes": item.get("notes", ""),
                    "published_at": doc.published_at,
                    "episode_guid": doc.episode_guid,
                    "retrieved_at": doc.retrieved_at,
                    "content_sha256": doc.content_sha256,
                    "audio_urls": doc.audio_urls[:10],
                    "hebrew_snippet_count": len(hebrew_line_snippets(doc.text)),
                    "matched_canonical_items": sum(1 for row in matches if row.get("canonical_item_id")),
                    "copyright_policy": "metadata_and_short_excerpts_only",
                }
            )
            all_matches.extend(matches)
            all_enrichment.extend(enrichment)
            all_lexical_evidence.extend(build_lexical_evidence(doc))

    linked_matches = [row for row in all_matches if row.get("canonical_item_id")]
    matched_canonical_items = {row["canonical_item_id"] for row in linked_matches}
    exact_matches = sum(1 for row in linked_matches if row.get("match_type") == "exact_lexical_entry")
    phrase_matches = sum(1 for row in linked_matches if row.get("match_type") == "normalized_hebrew_phrase")
    source_only_records = sum(1 for row in all_matches if not row.get("canonical_item_id"))

    manifest = {
        "schema": "mindtune.streetwise_hebrew_enrichment_import.v0.2",
        "generated_at": generated_at,
        "canonical_model": str(CITIZEN),
        "source_count": len(sources),
        "match_count": len(all_matches),
        "linked_match_count": len(linked_matches),
        "matched_canonical_item_count": len(matched_canonical_items),
        "exact_match_count": exact_matches,
        "phrase_match_count": phrase_matches,
        "source_only_record_count": source_only_records,
        "enrichment_count": len(all_enrichment),
        "lexical_evidence_count": len(all_lexical_evidence),
        "policy": {
            "canonical_corpus_modified": False,
            "mlf_core_modified": False,
            "content_storage": "metadata_and_short_excerpts_only",
            "review_required_before_display": True,
        },
    }
    write_json(out_dir / "STREETWISE_HEBREW_IMPORT_MANIFEST_v0.1.json", manifest)
    write_json(out_dir / "STREETWISE_HEBREW_RAW_SOURCES_v0.1.json", {"items": sources})
    write_json(out_dir / "STREETWISE_HEBREW_ENRICHMENT_CANDIDATES_v0.1.json", {"items": all_enrichment})
    write_jsonl(out_dir / "STREETWISE_HEBREW_MATCHES_v0.1.jsonl", all_matches)
    write_jsonl(out_dir / "STREETWISE_HEBREW_LEXICAL_EVIDENCE_v0.2.jsonl", all_lexical_evidence)
    write_csv(
        out_dir / "STREETWISE_HEBREW_REVIEW_QUEUE_v0.1.csv",
        all_matches,
        [
            "match_id",
            "source_id",
            "canonical_item_id",
            "deck",
            "hebrew",
            "italian",
            "match_type",
            "match_confidence",
            "context_excerpt",
            "review_status",
        ],
    )

    report = [
        "# Streetwise Hebrew Enrichment Import v0.2",
        "",
        f"Generated: `{generated_at}`",
        "",
        "This is not a canonical corpus import.",
        "",
        "- Citizen Cafe cards are not modified.",
        "- MLF Core is not modified.",
        "- Only metadata, source refs and short context excerpts are stored.",
        "- Human review is required before using any enrichment in exercises.",
        f"- Source episodes: **{len(sources)}**.",
        f"- Lexical evidence records: **{len(all_lexical_evidence)}**.",
        f"- Linked corpus matches: **{len(linked_matches)}** across **{len(matched_canonical_items)}** canonical items.",
        f"- Exact lexical matches: **{exact_matches}**.",
        f"- Controlled phrase matches: **{phrase_matches}**.",
        f"- Source-only episode records: **{source_only_records}**.",
    ]
    (out_dir / "STREETWISE_IMPORT_REPORT_v0.2.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(
        f"sources={len(sources)} lexical_evidence={len(all_lexical_evidence)} "
        f"matches={len(all_matches)} enrichment={len(all_enrichment)}"
    )
    print(f"out={out_dir}")


if __name__ == "__main__":
    main()
