"""
PinoyRice processing: HTML/text corpus + PDFs → CPT (one script).
Same flow as PhilRice: extract/clean/chunk, 1 file = 1 JSON.

Input:
  - pinoyrice_processed/pinoyrice_corpus.jsonl   (from scraper_pinoyrice.py)
  - pinoyrice_pdfs/*.pdf

Outputs:
  - Per-URL JSON (text): pinoyrice_processed/per_file_cpt/<safe_doc_id>.json
  - Chunked corpus (text): pinoyrice_processed/pinoyrice_corpus_chunked.jsonl
  - Per-PDF JSON: pinoyrice_processed/per_file_pdf/<stem>.json  (1 PDF = 1 JSON)
  - Corpus (PDFs): pinoyrice_processed/pinoyrice_pdfs_corpus.jsonl

Run: after scraper (or standalone). Scraper can call run() at end to process all.
"""
import os
import re
import json
from pathlib import Path

from rich.console import Console
from dotenv import load_dotenv

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

load_dotenv()
console = Console()

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PINOYRICE_PROCESSED_DIR = os.path.join(_PROJECT_DIR, "pinoyrice_processed")
PINOYRICE_PDFS_DIR = os.path.join(_PROJECT_DIR, "pinoyrice_pdfs")
PINOYRICE_INPUT_JSONL = os.path.join(PINOYRICE_PROCESSED_DIR, "pinoyrice_corpus.jsonl")
PINOYRICE_PER_FILE_CPT_DIR = os.path.join(PINOYRICE_PROCESSED_DIR, "per_file_cpt")
PINOYRICE_OUTPUT_JSONL = os.path.join(PINOYRICE_PROCESSED_DIR, "pinoyrice_corpus_chunked.jsonl")
PINOYRICE_PER_FILE_PDF_DIR = os.path.join(PINOYRICE_PROCESSED_DIR, "per_file_pdf")
PINOYRICE_PDFS_JSONL = os.path.join(PINOYRICE_PROCESSED_DIR, "pinoyrice_pdfs_corpus.jsonl")

SOURCE_NAME = "pinoyrice"

MIN_CHUNK_CHARS = int(os.getenv("PINOYRICE_MIN_CHUNK_CHARS", "100"))
MAX_CHUNK_CHARS = int(os.getenv("PINOYRICE_MAX_CHUNK_CHARS", "0"))  # 0 = no chunking

_UNWANTED_ENV = os.getenv(
    "PINOYRICE_UNWANTED_TEXTS",
    "HOME,RICE PRODUCTION,RICE VARIETIES,DOWNLOADS,SEED GROWERS,OFFLINE,Search for:,Menu -HOME,Are you satisfied with PINOYRICE KNOWLEDGE BANK?,uQuoted.com",
)
PINOYRICE_UNWANTED_SUBSTRINGS = [s.strip() for s in _UNWANTED_ENV.split(",") if s.strip()]
PINOYRICE_FOOTER_MARKERS = [
    "CONTACT US",
    "PHILRICE TEXT CENTER",
    "DEPARTMENT OF AGRICULTURE",
    "Are you satisfied with PINOYRICE KNOWLEDGE BANK?",
]

# Line-level noise: drop entire lines matching these (regex or substring)
PINOYRICE_NOISE_LINE_PATTERNS = [
    re.compile(r"^\s*Leave a Reply\s*$", re.I),
    re.compile(r"^\s*\d*\s*Reply\s*$", re.I),           # "0 Reply", "1 Reply", "2 Reply"
    re.compile(r"^\s*\d+\s*(year|month|day)s?\s+ago\s*$", re.I),
    re.compile(r"^\s*\d+\s*(year|month|day)\s+ago\s*$", re.I),
    re.compile(r"^\s*«\s*Previous\s*", re.I),
    re.compile(r"^\s*Next\s*»", re.I),
    re.compile(r"^\s*\d+\s*\.\.\.\s*\d+", re.I),         # "1 … 47 48 49" style pagination
    re.compile(r"^\s*Subscribe\s*$", re.I),
    re.compile(r"^\s*(Guest|Author|admin|Editor)\s*$", re.I),
    re.compile(r"^\s*Posted\s+on\s+", re.I),
    re.compile(r"^\s*Published\s+", re.I),
    re.compile(r"^\s*Share\s*(this|on)\s*", re.I),
]
# Substrings that make a line noise (case-insensitive)
PINOYRICE_NOISE_LINE_SUBSTRINGS = [
    "leave a reply", "0 reply", "1 reply", "2 reply", "replies",
    "years ago", "months ago", "days ago",
    "« previous", "next »", "subscribe", "post comment",
]


def _is_noise_line(line: str) -> bool:
    """True if line should be dropped (comment/reply/pagination/date junk)."""
    s = line.strip()
    if not s:
        return True
    lower = s.lower()
    if any(sub in lower for sub in PINOYRICE_NOISE_LINE_SUBSTRINGS):
        return True
    for pat in PINOYRICE_NOISE_LINE_PATTERNS:
        if pat.search(s):
            return True
    return False


def clean_pinoyrice_text(url: str, text: str) -> str:
    """
    Clean PinoyRice text: remove menus, headers, footers, reply/pagination noise.
    No fallback to original — if result is too short or junk, return "" so record is dropped.
    """
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines()]
    cleaned_lines: list[str] = []
    for ln in lines:
        if not ln:
            continue
        upper_ln = ln.upper()
        if any(marker.upper() in upper_ln for marker in PINOYRICE_FOOTER_MARKERS):
            break
        if any(sub.upper() in upper_ln for sub in PINOYRICE_UNWANTED_SUBSTRINGS):
            continue
        if _is_noise_line(ln):
            continue
        alpha_count = sum(c.isalpha() for c in ln)
        if len(ln) <= 80 and alpha_count >= 5 and ln == upper_ln:
            continue
        cleaned_lines.append(ln)
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines)).strip()
    # Do NOT keep original if too short — drop record (return "" so record_to_chunks returns [])
    if len(cleaned) < MIN_CHUNK_CHARS:
        return ""
    return cleaned


def _safe_id_from_url(url: str) -> str:
    """Base doc_id derived from URL path; safe for filenames."""
    try:
        # Strip scheme and query; keep path + maybe sluggy bits
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = (parsed.path or "").strip("/") or "pinoyrice"
    except Exception:
        path = "pinoyrice"
    return re.sub(r"[^\w\-.]", "_", path)[:120] or "pinoyrice"


def chunk_text(text: str, max_chars: int) -> list[str]:
    """Split text into chunks of at most max_chars, respecting blank-line paragraphs."""
    if not text:
        return []
    text = text.strip()
    if not max_chars or max_chars <= 0 or len(text) <= max_chars:
        return [text]

    out: list[str] = []
    paragraphs = text.split("\n\n")
    current = ""
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current) + len(p) + 2 <= max_chars:
            current = (current + "\n\n" + p).strip() if current else p
        else:
            if current:
                out.append(current)
            if len(p) > max_chars:
                # Hard split very long paragraphs
                for i in range(0, len(p), max_chars):
                    chunk = p[i : i + max_chars].strip()
                    if chunk:
                        out.append(chunk)
                current = ""
            else:
                current = p
    if current:
        out.append(current)
    return out


def record_to_chunks(record: dict) -> list[dict]:
    """Convert one raw scraper record into 1..N CPT chunk records."""
    raw_text = (record.get("text") or "").strip()
    text = clean_pinoyrice_text(record.get("url") or "", raw_text)
    if not text:
        return []

    base_id = record.get("doc_id") or _safe_id_from_url(record.get("url") or "")
    base_id = re.sub(r"[^\w\-.]", "_", base_id)[:120] or "pinoyrice"

    chunks = (
        chunk_text(text, MAX_CHUNK_CHARS)
        if MAX_CHUNK_CHARS and MAX_CHUNK_CHARS > 0
        else [text]
    )

    out: list[dict] = []
    if len(chunks) == 1:
        ch = chunks[0]
        if len(ch) < MIN_CHUNK_CHARS:
            return []
        out.append(
            {
                "text": ch,
                "input": ch,
                "content": ch,
                "source": SOURCE_NAME,
                "doc_id": base_id,
                "url": record.get("url"),
                "title": record.get("title"),
            }
        )
        return out

    for idx, ch in enumerate(chunks):
        if len(ch) < MIN_CHUNK_CHARS:
            continue
        out.append(
            {
                "text": ch,
                "input": ch,
                "content": ch,
                "source": SOURCE_NAME,
                "doc_id": f"{base_id}_chunk_{idx}",
                "url": record.get("url"),
                "title": record.get("title"),
            }
        )
    return out


# --- PDF processing (same pattern as processing_philrice.py) ---
NOISE_LINE_PATTERN_PDF = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)


def _table_to_text(table: list[list]) -> str:
    if not table:
        return ""
    return "\n".join(" | ".join(str(c or "").strip() for c in row) for row in table)


def _extract_tables_from_page(pdf_path: str, page_num: int) -> list[str]:
    if not HAS_PDFPLUMBER:
        return []
    out = []
    try:
        with pdfplumber.open(pdf_path) as doc:
            if 1 <= page_num <= len(doc.pages):
                for t in doc.pages[page_num - 1].extract_tables() or []:
                    txt = _table_to_text(t)
                    if txt.strip():
                        out.append(txt)
    except Exception:
        pass
    return out


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    if not HAS_PYMUPDF:
        return []
    out = []
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            text = doc[i].get_text()
            if HAS_PDFPLUMBER:
                tables = _extract_tables_from_page(pdf_path, i + 1)
                if tables:
                    text = (text.strip() if text else "") + "\n\n[Table]\n" + "\n\n[Table]\n".join(tables)
            if text and text.strip():
                out.append({"page": i + 1, "text": text.strip()})
        doc.close()
    except Exception as e:
        console.print(f"[yellow]PDF {pdf_path}: {e}[/yellow]")
    return out


def detect_noise_lines_pdf(pages: list[dict], min_freq_ratio: float = 0.3, max_line_len: int = 120) -> set[str]:
    if not pages:
        return set()
    from collections import Counter
    total = len(pages)
    cnt: Counter = Counter()
    for item in pages:
        seen = set()
        for line in item["text"].split("\n"):
            s = line.strip()
            if s and s not in seen:
                cnt[s] += 1
                seen.add(s)
    threshold = max(2, int(total * min_freq_ratio))
    return {line for line, c in cnt.items() if c >= threshold and len(line) <= max_line_len}


def clean_pdf_text(text: str, noise_lines: set[str] | None) -> str:
    if not text or not text.strip():
        return ""
    text = re.sub(r"\r\n", "\n", text)
    text = NOISE_LINE_PATTERN_PDF.sub("", text)
    if noise_lines:
        for line in noise_lines:
            text = re.sub(r"(?m)^" + re.escape(line) + r"\s*$", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def chunk_text_pdf(text: str, max_chars: int) -> list[str]:
    if not max_chars or max_chars <= 0 or len(text) <= max_chars:
        return [text] if text.strip() else []
    out = []
    current = ""
    for p in text.split("\n\n"):
        if len(current) + len(p) + 2 <= max_chars:
            current = (current + "\n\n" + p).strip() if current else p
        else:
            if current:
                out.append(current)
            current = p if len(p) <= max_chars else ""
            if len(p) > max_chars:
                for i in range(0, len(p), max_chars):
                    out.append(p[i : i + max_chars].strip())
    if current:
        out.append(current)
    return out


def process_one_pdf(pdf_path: str) -> list[dict]:
    pages = extract_text_from_pdf(pdf_path)
    if not pages:
        return []
    noise = detect_noise_lines_pdf(pages)
    records = []
    base_id = Path(pdf_path).stem
    fname = os.path.basename(pdf_path)
    for item in pages:
        text = clean_pdf_text(item["text"], noise)
        if len(text) < MIN_CHUNK_CHARS:
            continue
        page_num = item["page"]
        if not MAX_CHUNK_CHARS:
            records.append({
                "text": text, "input": text, "content": text,
                "source": SOURCE_NAME, "doc_id": f"{base_id}_page_{page_num}",
                "filename": fname, "page": page_num,
            })
        else:
            for j, ch in enumerate(chunk_text_pdf(text, MAX_CHUNK_CHARS)):
                if len(ch) >= MIN_CHUNK_CHARS:
                    records.append({
                        "text": ch, "input": ch, "content": ch,
                        "source": SOURCE_NAME, "doc_id": f"{base_id}_page_{page_num}_chunk_{j}",
                        "filename": fname, "page": page_num,
                    })
    return records


def run_text():
    """Process corpus JSONL → chunked + per_file_cpt. Dedupe by URL (first only). Clear per_file_cpt first."""
    if not os.path.isfile(PINOYRICE_INPUT_JSONL):
        console.print(f"[dim]No corpus JSONL; skip text processing.[/dim]")
        return 0
    console.print(f"[dim]Text: {PINOYRICE_INPUT_JSONL} → chunked + per_file_cpt[/dim]")
    os.makedirs(PINOYRICE_PROCESSED_DIR, exist_ok=True)
    os.makedirs(PINOYRICE_PER_FILE_CPT_DIR, exist_ok=True)
    for f in Path(PINOYRICE_PER_FILE_CPT_DIR).glob("*.json"):
        try:
            f.unlink()
        except Exception:
            pass

    seen_urls: set[str] = set()
    total_in = 0
    total_out = 0
    per_url_buffers: dict[str, list[dict]] = {}

    with open(PINOYRICE_INPUT_JSONL, "r", encoding="utf-8") as f_in, open(
        PINOYRICE_OUTPUT_JSONL, "w", encoding="utf-8"
    ) as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            total_in += 1
            url = (raw.get("url") or "").strip()
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            chunks = record_to_chunks(raw)
            if not chunks:
                continue
            for ch in chunks:
                f_out.write(json.dumps(ch, ensure_ascii=False) + "\n")
            total_out += len(chunks)
            key = _safe_id_from_url(url) if url else (raw.get("doc_id") or f"rec_{total_in}")
            if key not in per_url_buffers:
                per_url_buffers[key] = []
            per_url_buffers[key].extend(chunks)

    for key, records in per_url_buffers.items():
        safe = re.sub(r"[^\w\-.]", "_", key)[:180] or "pinoyrice"
        path = Path(PINOYRICE_PER_FILE_CPT_DIR) / f"{safe}.json"
        try:
            with open(path, "w", encoding="utf-8") as jf:
                json.dump(records, jf, ensure_ascii=False, indent=2)
        except Exception as e:
            console.print(f"[yellow]Write {path.name}: {e}[/yellow]")
    return total_out


def run_pdfs():
    """Process pinoyrice_pdfs/*.pdf → per_file_pdf (1 PDF = 1 JSON) + pinoyrice_pdfs_corpus.jsonl."""
    if not HAS_PYMUPDF:
        return 0
    if not os.path.isdir(PINOYRICE_PDFS_DIR):
        return 0
    pdf_files = sorted(Path(PINOYRICE_PDFS_DIR).glob("*.pdf"))
    if not pdf_files:
        return 0
    os.makedirs(PINOYRICE_PER_FILE_PDF_DIR, exist_ok=True)
    total = 0
    with open(PINOYRICE_PDFS_JSONL, "w", encoding="utf-8") as corpus_f:
        for pdf_path in pdf_files:
            records = process_one_pdf(str(pdf_path))
            safe_stem = re.sub(r"[^\w\-.]", "_", pdf_path.stem)[:180]
            per_path = Path(PINOYRICE_PER_FILE_PDF_DIR) / f"{safe_stem}.json"
            with open(per_path, "w", encoding="utf-8") as jf:
                json.dump(records, jf, ensure_ascii=False, indent=2)
            for r in records:
                corpus_f.write(json.dumps(r, ensure_ascii=False) + "\n")
            total += len(records)
    return total


def run():
    """Run text processing then PDF processing. Call after scraper or standalone."""
    console.rule("[bold cyan]PinoyRice processing (text + PDF)")
    text_out = run_text()
    pdf_out = run_pdfs()
    console.rule("[bold green]Done")
    console.print(f"Text CPT chunks: [green]{text_out}[/green]")
    console.print(f"PDF CPT chunks: [green]{pdf_out}[/green]")
    console.print(f"Per-URL JSON: [cyan]{PINOYRICE_PER_FILE_CPT_DIR}[/cyan]")
    console.print(f"Per-PDF JSON: [cyan]{PINOYRICE_PER_FILE_PDF_DIR}[/cyan]")


if __name__ == "__main__":
    run()

