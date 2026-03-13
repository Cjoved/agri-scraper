"""
PhilRice News .txt -> CPT JSON.

Basahin lahat ng philrice_news/*.txt (output ng scraper_philrice_news.py),
gawing CPT format (text, input, content, source, doc_id, filename) at isulat:

  1) Per-file JSON: philrice_news_processed/per_file/<stem>.json  (array ng records; chunked kung lampas MAX)
  2) Corpus: philrice_news_processed/philrice_news_corpus.jsonl   (one JSON object per line)

Walang "page". Kung lampas sa MAX_CHUNK_CHARS, hahatiin by paragraph -> doc_id = stem_chunk_0, ...
Source .txt files are kept as backup; not deleted after processing.
"""
import os
import re
import json
from pathlib import Path

from rich.console import Console
from dotenv import load_dotenv

load_dotenv()
console = Console()

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PHILRICE_NEWS_DIR = os.path.join(_PROJECT_DIR, "philrice_news")
PHILRICE_NEWS_PROCESSED_DIR = os.path.join(_PROJECT_DIR, "philrice_news_processed")
PHILRICE_NEWS_PER_FILE_DIR = os.path.join(PHILRICE_NEWS_PROCESSED_DIR, "per_file")
OUTPUT_JSONL = os.path.join(PHILRICE_NEWS_PROCESSED_DIR, "philrice_news_corpus.jsonl")

SOURCE_NAME = "philrice_news"

# Chunking: walang page sa news, so kung masyadong mahaba i-split by paragraph
MIN_CHUNK_CHARS = int(os.getenv("PHILRICE_NEWS_MIN_CHUNK_CHARS", "100"))
MAX_CHUNK_CHARS = int(os.getenv("PHILRICE_NEWS_MAX_CHUNK_CHARS", "0"))  # 0 = no split, one record per article
# Keep .txt as backup (like PHILRICE_DELETE_PDF_AFTER_CLEAN=false). We do not delete .txt after process.
DELETE_TXT_AFTER_PROCESS = os.getenv("PHILRICE_NEWS_DELETE_TXT_AFTER_PROCESS", "false").strip().lower() in ("true", "1", "yes")


def chunk_text(text: str, max_chars: int) -> list[str]:
    """Split text into chunks of at most max_chars (by paragraph where possible)."""
    if not max_chars or max_chars <= 0 or len(text) <= max_chars:
        return [text] if text.strip() else []
    out = []
    paragraphs = text.split("\n\n")
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 2 <= max_chars:
            current = (current + "\n\n" + p).strip() if current else p
        else:
            if current:
                out.append(current)
            if len(p) > max_chars:
                for i in range(0, len(p), max_chars):
                    out.append(p[i : i + max_chars].strip())
                current = ""
            else:
                current = p
    if current:
        out.append(current)
    return out


def txt_to_cpt_records(txt_path: str) -> list[dict]:
    """
    Read one .txt file and return list of CPT records.
    Kung MAX_CHUNK_CHARS > 0 at lampas ang text, split by paragraph → doc_id = stem_chunk_0, stem_chunk_1, ...
    Walang "page" field (news = isang article, walang page number).
    """
    path = Path(txt_path)
    if not path.is_file() or path.suffix.lower() != ".txt":
        return []
    try:
        text = path.read_text(encoding="utf-8").strip()
    except Exception as e:
        console.print(f"[yellow]Read failed {path.name}: {e}[/yellow]")
        return []
    if not text:
        return []
    stem = path.stem
    base_id = re.sub(r"[^\w\-.]", "_", stem)[:120] or "philrice_news_unknown"

    def make_record(doc_id: str, chunk_text: str) -> dict:
        return {
            "text": chunk_text,
            "input": chunk_text,
            "content": chunk_text,
            "source": SOURCE_NAME,
            "doc_id": doc_id,
            "filename": path.name,
        }

    if MAX_CHUNK_CHARS > 0 and len(text) > MAX_CHUNK_CHARS:
        chunks = chunk_text(text, MAX_CHUNK_CHARS)
        records = []
        for j, ch in enumerate(chunks):
            if len(ch) < MIN_CHUNK_CHARS:
                continue
            records.append(make_record(f"{base_id}_chunk_{j}", ch))
        return records
    if len(text) < MIN_CHUNK_CHARS:
        return []
    return [make_record(base_id, text)]


def run():
    """Process all philrice_news/*.txt → per-file JSON + philrice_news_corpus.jsonl."""
    if not os.path.isdir(PHILRICE_NEWS_DIR):
        console.print(f"[yellow]Folder not found: {PHILRICE_NEWS_DIR}[/yellow]")
        console.print("[dim]Run scraper_philrice_news.py first to generate .txt files.[/dim]")
        return

    os.makedirs(PHILRICE_NEWS_PROCESSED_DIR, exist_ok=True)
    os.makedirs(PHILRICE_NEWS_PER_FILE_DIR, exist_ok=True)

    txt_files = sorted(Path(PHILRICE_NEWS_DIR).glob("*.txt"))
    if not txt_files:
        console.print(f"[yellow]No .txt files in {PHILRICE_NEWS_DIR}[/yellow]")
        return

    console.rule("[bold cyan]PhilRice News .txt -> CPT JSON")
    console.print(f"Processing {len(txt_files)} .txt files -> per-file JSON + corpus JSONL.")
    if MAX_CHUNK_CHARS > 0:
        console.print(f"[dim]Chunking: max {MAX_CHUNK_CHARS} chars, min {MIN_CHUNK_CHARS} chars (no page)[/dim]")
    else:
        console.print("[dim]No chunking (MAX_CHUNK_CHARS=0): one record per article.[/dim]")

    total = 0
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as corpus_f:
        for i, txt_path in enumerate(txt_files):
            path_str = str(txt_path)
            records = txt_to_cpt_records(path_str)
            if not records:
                continue
            console.print(f"[dim]({i + 1}/{len(txt_files)}) {txt_path.name} -> {len(records)} chunk(s)[/dim]")
            safe_stem = re.sub(r"[^\w\-.]", "_", txt_path.stem)[:180]
            per_file_path = Path(PHILRICE_NEWS_PER_FILE_DIR) / f"{safe_stem}.json"
            with open(per_file_path, "w", encoding="utf-8") as jf:
                json.dump(records, jf, ensure_ascii=False, indent=2)
            for r in records:
                corpus_f.write(json.dumps(r, ensure_ascii=False) + "\n")
            total += len(records)

    console.rule("[bold green]Done")
    console.print(f"Per-file JSON: [cyan]{PHILRICE_NEWS_PER_FILE_DIR}[/cyan]")
    console.print(f"Corpus JSONL: [cyan]{OUTPUT_JSONL}[/cyan]")
    console.print(f"Total CPT records (chunks): [green]{total}[/green]")


if __name__ == "__main__":
    run()
