"""
PhilRice PDF processing – hiwalay sa OpenSTAT (processing.py).
Extract text + tables from PDFs in philrice_pdfs/, clean, chunk.

OUTPUTS:
  1) Per-file JSON (paglinis at CPT format): philrice_processed/per_file/<filename>.json
     – Isang .json bawat PDF; array ng chunk objects. Pwedeng i-edit/linisin bago i-merge.
  2) Merged corpus: philrice_processed/philrice_corpus.jsonl (JSONL, one object per line).

CPT FORMAT (per chunk): "text", "input", "content" (same value); "source", "doc_id", "filename", "page".
Noise: standalone page-number lines (^\s*\d{1,4}\s*$) are removed in clean_text.
Validate: python validate_philrice_jsonl.py philrice_processed/philrice_corpus.jsonl
"""
import os
import re
import json
from pathlib import Path

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

from rich.console import Console
from dotenv import load_dotenv

load_dotenv()
console = Console()

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PHILRICE_PDFS_DIR = os.path.join(_PROJECT_DIR, "philrice_pdfs")
PHILRICE_PROCESSED_DIR = os.path.join(_PROJECT_DIR, "philrice_processed")
PHILRICE_PER_FILE_DIR = os.path.join(PHILRICE_PROCESSED_DIR, "per_file")
OUTPUT_JSONL = os.path.join(PHILRICE_PROCESSED_DIR, "philrice_corpus.jsonl")

CHUNK_BY_PAGE = True
MIN_CHUNK_CHARS = int(os.getenv("PHILRICE_MIN_CHUNK_CHARS", "100"))
MAX_CHUNK_CHARS = int(os.getenv("PHILRICE_MAX_CHUNK_CHARS", "0"))
DELETE_PDF_AFTER_CLEAN = os.getenv("PHILRICE_DELETE_PDF_AFTER_CLEAN", "").strip().lower() in ("true", "1", "yes")

# Noise lines: standalone page numbers (1–9999), tinatanggal para malinis ang CPT text
NOISE_LINE_PATTERN = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)


def _table_to_text(table: list[list]) -> str:
    """Convert a table (list of rows) to readable text (markdown-style)."""
    if not table:
        return ""
    lines = []
    for row in table:
        cells = [str(c or "").strip() for c in row]
        lines.append(" | ".join(cells))
    return "\n".join(lines)


def extract_tables_from_page(pdf_path: str, page_num: int) -> list[str]:
    """Extract tables from one page using pdfplumber. Returns list of table-as-text strings."""
    if not HAS_PDFPLUMBER:
        return []
    out = []
    try:
        with pdfplumber.open(pdf_path) as doc:
            if page_num < 1 or page_num > len(doc.pages):
                return []
            page = doc.pages[page_num - 1]
            tables = page.extract_tables()
            if tables:
                for t in tables:
                    txt = _table_to_text(t)
                    if txt.strip():
                        out.append(txt)
    except Exception:
        pass
    return out


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text per page from one PDF. If pdfplumber is available, also extract
    tables per page and append to page text. Returns list of {"page": 1-based, "text": "..."}.
    """
    if not HAS_PYMUPDF:
        console.print("[red]PyMuPDF not installed. Run: pip install pymupdf[/red]")
        return []
    out = []
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text()
            if HAS_PDFPLUMBER:
                tables_text = extract_tables_from_page(pdf_path, i + 1)
                if tables_text:
                    text = (text.strip() if text else "") + "\n\n[Table]\n" + "\n\n[Table]\n".join(tables_text)
            if text and text.strip():
                out.append({"page": i + 1, "text": text.strip()})
        doc.close()
    except Exception as e:
        console.print(f"[yellow]Error reading {pdf_path}: {e}[/yellow]")
    return out


def detect_noise_lines(pages: list[dict], min_freq_ratio: float = 0.3, max_line_len: int = 120) -> set[str]:
    """
    Detect running headers/footers by frequency across pages of a single PDF.
    A line is noise if it appears in >= min_freq_ratio of all pages AND is short enough
    to be a header/footer (not actual content).
    General approach: no hardcoded text — works for any PhilRice PDF type
    (R&D Highlights, e-Magazine, RS4DM, References, Milestones, etc.)
    """
    if not pages:
        return set()
    from collections import Counter
    total_pages = len(pages)
    line_page_count: Counter = Counter()
    for item in pages:
        seen_in_page: set[str] = set()
        for line in item["text"].split("\n"):
            stripped = line.strip()
            if stripped and stripped not in seen_in_page:
                line_page_count[stripped] += 1
                seen_in_page.add(stripped)
    noise: set[str] = set()
    threshold = max(2, int(total_pages * min_freq_ratio))
    for line, count in line_page_count.items():
        if count >= threshold and len(line) <= max_line_len:
            noise.add(line)
    return noise


def clean_text(text: str, noise_lines: set[str] | None = None) -> str:
    """
    Cleanup: normalize whitespace, remove standalone page numbers,
    and strip detected running header/footer noise lines.
    noise_lines is produced by detect_noise_lines() — general, not hardcoded.
    """
    if not text or not text.strip():
        return ""
    text = re.sub(r"\r\n", "\n", text)
    # Remove standalone page numbers (bare digits on their own line)
    text = NOISE_LINE_PATTERN.sub("", text)
    # Remove running headers/footers detected by frequency analysis
    if noise_lines:
        for line in noise_lines:
            text = re.sub(r"(?m)^" + re.escape(line) + r"\s*$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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


def process_one_pdf(pdf_path: str, source_name: str) -> list[dict]:
    """
    Extract, clean, chunk one PDF. Returns list of records for JSONL (CPT format).
    """
    pages = extract_text_from_pdf(pdf_path)
    if not pages:
        return []
    # Detect noise lines (running headers/footers) across ALL pages of this PDF first.
    # General: no hardcoded text — works for any PhilRice document type.
    noise_lines = detect_noise_lines(pages)
    if noise_lines:
        console.print(f"[dim]  Noise stripped ({len(noise_lines)} line/s): {sorted(noise_lines)[:3]}{'...' if len(noise_lines) > 3 else ''}[/dim]")
    records = []
    base_id = Path(pdf_path).stem
    for item in pages:
        page_num = item["page"]
        text = clean_text(item["text"], noise_lines=noise_lines)
        if len(text) < MIN_CHUNK_CHARS:
            continue

        def make_record(doc_id: str, chunk_text: str) -> dict:
            return {
                "text": chunk_text,
                "input": chunk_text,
                "content": chunk_text,
                "source": source_name,
                "doc_id": doc_id,
                "filename": os.path.basename(pdf_path),
                "page": page_num,
            }

        if CHUNK_BY_PAGE and not MAX_CHUNK_CHARS:
            records.append(make_record(f"{base_id}_page_{page_num}", text))
        else:
            chunks = chunk_text(text, MAX_CHUNK_CHARS) if MAX_CHUNK_CHARS else [text]
            for j, chunk in enumerate(chunks):
                if len(chunk) < MIN_CHUNK_CHARS:
                    continue
                records.append(make_record(f"{base_id}_page_{page_num}_chunk_{j}", chunk))
    return records


def run():
    """Process all PDFs: one JSON per PDF (per_file/) for cleaning + CPT, then merged corpus (philrice_corpus.jsonl)."""
    if not HAS_PYMUPDF:
        console.print("[red]Install PyMuPDF first: pip install pymupdf[/red]")
        return
    if HAS_PDFPLUMBER:
        console.print("[dim]Table extraction enabled (pdfplumber).[/dim]")
    else:
        console.print("[dim]Install pdfplumber for table extraction: pip install pdfplumber[/dim]")
    if not os.path.isdir(PHILRICE_PDFS_DIR):
        console.print(f"[yellow]Folder not found: {PHILRICE_PDFS_DIR}[/yellow]")
        console.print("[dim]Run scraper_philrice.py first to download PDFs.[/dim]")
        return

    os.makedirs(PHILRICE_PROCESSED_DIR, exist_ok=True)
    os.makedirs(PHILRICE_PER_FILE_DIR, exist_ok=True)
    all_pdfs = list(Path(PHILRICE_PDFS_DIR).glob("*.pdf"))
    pdf_files = list(all_pdfs)
    if not pdf_files:
        console.print(f"[yellow]No PDFs to process in {PHILRICE_PDFS_DIR}[/yellow]")
        return

    console.rule("[bold cyan]PhilRice PDF processing")
    console.print(f"Processing {len(pdf_files)} PDFs → per-file JSON + corpus JSONL.")
    if DELETE_PDF_AFTER_CLEAN:
        console.print("[yellow]PHILRICE_DELETE_PDF_AFTER_CLEAN=true: PDFs will be deleted after successful processing.[/yellow]")
    total_records = 0
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as corpus_f:
        for i, pdf_path in enumerate(pdf_files):
            path_str = str(pdf_path)
            console.print(f"[dim]({i + 1}/{len(pdf_files)}) {pdf_path.name}[/dim]")
            records = process_one_pdf(path_str, source_name="philrice")
            safe_stem = re.sub(r"[^\w\-.]", "_", pdf_path.stem)[:180]
            per_file_path = Path(PHILRICE_PER_FILE_DIR) / f"{safe_stem}.json"
            with open(per_file_path, "w", encoding="utf-8") as jf:
                json.dump(records, jf, ensure_ascii=False, indent=2)
            for r in records:
                corpus_f.write(json.dumps(r, ensure_ascii=False) + "\n")
            total_records += len(records)
            if DELETE_PDF_AFTER_CLEAN and path_str and os.path.isfile(path_str):
                try:
                    os.remove(path_str)
                    console.print(f"[dim]  Deleted (freed space): {pdf_path.name}[/dim]")
                except Exception as e:
                    console.print(f"[yellow]  Could not delete {pdf_path.name}: {e}[/yellow]")
    console.rule("[bold green]Done")
    console.print(f"Per-file JSON: [cyan]{PHILRICE_PER_FILE_DIR}[/cyan]")
    console.print(f"Merged corpus: [cyan]{OUTPUT_JSONL}[/cyan]")
    console.print(f"Total chunks/documents: [green]{total_records}[/green]")


if __name__ == "__main__":
    run()