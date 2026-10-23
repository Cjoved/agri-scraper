# Project structure (senior-level)

## src/ — Application code

| Path | Role |
|------|------|
| **src/config.py** | `PROJECT_ROOT`, `DATA_DIR`, `data_path()` — all paths under `data/` |
| **src/agri_corpus/** | Text chunking, PDF extract/clean, CPT format, scraper utils |
| **src/utils/** | Network (Playwright retry, require_internet), bypass (FlareSolverr), database (MySQL) |
| **src/services/** | Processing: PhilRice, PhilRice News, PinoyRice, **OpenSTAT** (Excel → CSV + MySQL) |
| **src/scrapers/** | PhilRice PDF, PhilRice News, PinoyRice, **OpenSTAT** (PSA agri-price) scrapers |
| **src/scripts/** | One-off: migrate_pinoyrice_txt, inspect_all_philrice_links, inspect_emagazine_links, validate_philrice_jsonl |
| **src/flaresolverr_ui/** | FlareSolverr status/test web UI (`python -m src.flaresolverr_ui`) |

## data/ — All scraped & processed output

- **data/philrice_pdfs/** — PhilRice PDF downloads  
- **data/philrice_processed/** — PhilRice corpus JSONL + per-file JSON  
- **data/philrice_news/** — PhilRice News .txt  
- **data/philrice_news_processed/** — PhilRice News corpus JSONL  
- **data/pinoyrice_pdfs/** — PinoyRice PDF downloads  
- **data/pinoyrice_processed/** — PinoyRice corpus + chunked JSONL + per_file_cpt, per_file_pdf  
- **data/pinoyrice_txt/** — PinoyRice raw page .txt  
- **data/checkpoints/** — philrice, philrice_news, pinoyrice, **openstat_checkpoint.json**  
- **data/openstat_downloads/** — OpenSTAT Excel downloads  
- **data/manual_downloads/** — Manual OpenSTAT Excel (when Cloudflare blocks)  
- **data/screenshots/** — OpenSTAT failure screenshots  
- **data/error_logs/** — OpenSTAT error HTML  

**Migration:** If you had data in the project root (e.g. `philrice_processed/`), move those folders into `data/` so the new layout is used.

## Root (minimal)

Only these stay at project root:
- **main.py** — Full main logic (PhilRice / PhilRice News / PinoyRice / OpenSTAT via .env). Run: `python main.py`
- **requirements.txt** — Python dependencies
- **docker-compose.yml** — Docker setup
- **README.md** — Short intro; full docs in **docs/**
- **docs/** — All documentation (.md, .txt)

All code lives under **src/** (scrapers, services, utils, agri_corpus, scripts, flaresolverr_ui).

## Run from project root

```bash
python main.py
# Single scraper/processing:
python -m src.scrapers.philrice
python -m src.scrapers.pinoyrice
python -m src.scrapers.openstat
python -m src.services.philrice
python -m src.services.pinoyrice
python -m src.services.openstat   # process_manual_downloads() for manual Excel
# Scripts:
python -m src.scripts.migrate_pinoyrice_txt
python -m src.scripts.inspect_all_philrice_links
python -m src.scripts.validate_philrice_jsonl
# FlareSolverr UI:
python -m src.flaresolverr_ui
```
