# src — Application code (senior-level layout)

- **config** — `PROJECT_ROOT`, `DATA_DIR`, `data_path()` — single source for paths; all I/O under `data/`.
- **agri_corpus** — Shared CPT/scraper helpers: text chunking, PDF extract/clean, CPT record format, checkpoint/URL utils.
- **utils** — Network (wait_for_selector_with_retry, require_internet), bypass (FlareSolverr), database (MySQL).
- **services** — Processing pipelines: PhilRice PDFs, PhilRice News .txt, PinoyRice (text + PDF). All read/write under `data/`.
- **scrapers** — Still at project root (`scraper_philrice.py`, `scraper_pinoyrice.py`, `scraper_philrice_news.py`) but use `src.config.data_path` and `src.utils` / `src.agri_corpus`; outputs go to `data/`.

Run from **project root** (OpenStatv2):
- `python main.py` — entry point (PhilRice / PhilRice News / PinoyRice / OpenSTAT via .env).
- `python processing_philrice.py` — thin wrapper → `src.services.philrice.run()`.
- `python scraper_philrice.py` — scrapes to `data/philrice_pdfs/`, checkpoint in `data/checkpoints/`.
