"""
Prism processing pipeline: raw scrape → CPT / chunked JSONL (tulad ng pinoyrice / irri).

Input: data/prism_processed/prism_corpus.jsonl (galing sa scraper)
Output: i-configure kapag kailangan (hal. prism_corpus_chunked.jsonl sa prism_processed/).
"""
import os

from dotenv import load_dotenv
from rich.console import Console

from src.config import data_path

load_dotenv()
console = Console()

PRISM_PROCESSED_DIR = data_path("prism_processed")
PRISM_INPUT_JSONL = data_path("prism_processed", "prism_corpus.jsonl")
PRISM_OUTPUT_JSONL = data_path("prism_processed", "prism_corpus_chunked.jsonl")

SOURCE_NAME = "prism"
MIN_CHUNK_CHARS = int(os.getenv("PRISM_MIN_CHUNK_CHARS", "100"))
MAX_CHUNK_CHARS = int(os.getenv("PRISM_MAX_CHUNK_CHARS", "0"))


def run():
    console.rule("[bold cyan]Prism – Process[/bold cyan]")
    console.print(f"[dim]Input: {PRISM_INPUT_JSONL}[/dim]")
    console.print(f"[dim]Planned output: {PRISM_OUTPUT_JSONL}[/dim]")
    os.makedirs(PRISM_PROCESSED_DIR, exist_ok=True)
    # TODO: basahin ang JSONL, linisin/chunk, gaya ng src.services.pinoyrice o irri
    console.print("[yellow]Processing: i-implement pa (chunking / CPT records).[/yellow]")


if __name__ == "__main__":
    run()
