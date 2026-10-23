"""Scraper source definitions for the Streamlit UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class OutputPath:
    label: str
    path: Path
    kind: str = "file"  # file | dir | pattern


@dataclass(frozen=True)
class ScraperSource:
    key: str
    label: str
    env: dict[str, str]
    outputs: list[OutputPath] = field(default_factory=list)
    warning: str | None = None


def _all_false() -> dict[str, str]:
    return {
        "PHILRICE": "false",
        "PHILRICE_NEWS": "false",
        "PINOYRICE": "false",
        "OPENSTAT": "false",
        "IRRI": "false",
        "PRISM": "false",
        "PRISM_JOB": "",
    }


def _env(**overrides: str) -> dict[str, str]:
    base = _all_false()
    base.update(overrides)
    return base


SCRAPER_SOURCES: list[ScraperSource] = [
    ScraperSource(
        key="philrice",
        label="PhilRice PDFs",
        env=_env(PHILRICE="true"),
        outputs=[
            OutputPath("Corpus JSONL", PROJECT_ROOT / "data" / "philrice_processed" / "philrice_corpus.jsonl"),
            OutputPath("Per-file JSON", PROJECT_ROOT / "data" / "philrice_processed" / "per_file", kind="dir"),
            OutputPath("Checkpoint", PROJECT_ROOT / "data" / "checkpoints" / "philrice_checkpoint.json"),
        ],
    ),
    ScraperSource(
        key="philrice_news",
        label="PhilRice News",
        env=_env(PHILRICE_NEWS="true"),
        outputs=[
            OutputPath("Raw articles", PROJECT_ROOT / "data" / "philrice_news", kind="dir"),
            OutputPath("Corpus JSONL", PROJECT_ROOT / "data" / "philrice_news_processed" / "philrice_news_corpus.jsonl"),
            OutputPath("Checkpoint", PROJECT_ROOT / "data" / "checkpoints" / "philrice_news_checkpoint.json"),
        ],
        warning="Requires stable access to philrice.gov.ph (timeouts may occur).",
    ),
    ScraperSource(
        key="pinoyrice",
        label="PinoyRice",
        env=_env(PINOYRICE="true"),
        outputs=[
            OutputPath("Text corpus", PROJECT_ROOT / "data" / "pinoyrice_processed" / "pinoyrice_corpus.jsonl"),
            OutputPath("PDF corpus", PROJECT_ROOT / "data" / "pinoyrice_processed" / "pinoyrice_pdfs_corpus.jsonl"),
            OutputPath("Checkpoint", PROJECT_ROOT / "data" / "checkpoints" / "pinoyrice_checkpoint.json"),
        ],
    ),
    ScraperSource(
        key="irri",
        label="IRRI (Philippines)",
        env=_env(IRRI="true"),
        outputs=[
            OutputPath("Raw text", PROJECT_ROOT / "data" / "irri_processed" / "text", kind="dir"),
            OutputPath("Corpus JSONL", PROJECT_ROOT / "data" / "irri_processed" / "irri_corpus.jsonl"),
            OutputPath("PDFs", PROJECT_ROOT / "data" / "irri_pdfs", kind="dir"),
            OutputPath("Checkpoint", PROJECT_ROOT / "data" / "checkpoints" / "irri_checkpoint.json"),
        ],
        warning="May hit 403/rate limits; retries are configured in the scraper.",
    ),
    ScraperSource(
        key="openstat",
        label="OpenSTAT (PSA)",
        env=_env(OPENSTAT="true"),
        outputs=[
            OutputPath("Excel downloads", PROJECT_ROOT / "data" / "openstat_downloads", kind="dir"),
            OutputPath(
                "Combined CSV (Desktop)",
                Path.home() / "Desktop" / "Agri-Price-Data_Files",
                kind="dir",
            ),
            OutputPath("Checkpoint", PROJECT_ROOT / "data" / "checkpoints" / "openstat_checkpoint.json"),
        ],
        warning="Uses a visible browser; Cloudflare/FlareSolverr may be required.",
    ),
    ScraperSource(
        key="prism_scrape",
        label="PRiSM — dashboard scrape",
        env=_env(PRISM="true", PRISM_JOB=""),
        outputs=[
            OutputPath("Corpus JSONL", PROJECT_ROOT / "data" / "prism_processed" / "prism_corpus.jsonl"),
            OutputPath("Text pages", PROJECT_ROOT / "data" / "prism_txt", kind="dir"),
            OutputPath("Checkpoint", PROJECT_ROOT / "data" / "checkpoints" / "prism_checkpoint.json"),
        ],
        warning="Requires Scrapling (`pip install -r requirements-prism.txt` + scrapling install).",
    ),
    ScraperSource(
        key="prism_yield",
        label="PRiSM — yield CSV export",
        env=_env(PRISM="true", PRISM_JOB="export_yield_csv"),
        outputs=[
            OutputPath("Yield CSV", PROJECT_ROOT / "data" / "prism_processed" / "prism_yield_export.csv"),
            OutputPath(
                "Checkpoint",
                PROJECT_ROOT / "data" / "checkpoints" / "prism_yield_export_checkpoint.json",
            ),
        ],
        warning="HTTP export only; can take a long time (rate limits / cooldowns).",
    ),
]

SOURCE_BY_KEY = {s.key: s for s in SCRAPER_SOURCES}
SOURCE_LABELS = [s.label for s in SCRAPER_SOURCES]


def get_source_by_label(label: str) -> ScraperSource | None:
    for s in SCRAPER_SOURCES:
        if s.label == label:
            return s
    return None
