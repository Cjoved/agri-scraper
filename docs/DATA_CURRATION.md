## Data Curation Overview

This document describes how raw web data flows through the scrapers and services in this repository to produce cleaned, model‑ready CPT corpora.

Supported sources:
- PSA OpenSTAT (Philippines)
- PhilRice PDFs
- PhilRice News
- PinoyRice portal
- IRRI News (All News, `Country = Philippines`)

---

## 1. High‑level Flow

1. **Scrape**
   - Playwright scrapers in `src/scrapers/` fetch content from source websites.
   - Raw outputs: `.txt` files and PDFs under `data/` (and `pinoyrice_processed/`).

2. **Clean + Transform**
   - Service modules in `src/services/` parse and clean `.txt` files, then build CPT records.
   - Cleaning is source‑specific (e.g. remove navigation, “SHARE”, footer contact blocks).

3. **Consume**
   - Downstream systems (RAG, LLM training, analytics) read from JSONL corpora:
     - `data/philrice_processed/philrice_corpus.jsonl`
     - `philrice_news_processed/philrice_news_corpus.jsonl`
     - `data/pinoyrice_processed/pinoyrice_corpus.jsonl`
     - `pinoyrice_processed/pinoyrice_pdfs_corpus.jsonl`
     - `data/irri_processed/irri_corpus.jsonl`

All corpora share a consistent CPT schema (see §4).

---

## 2. Running Pipelines

### 2.1 Environment flags

Exactly **one** of these flags should be `true` per run:

```env
PHILRICE=true        # PhilRice PDFs
PHILRICE_NEWS=false  # PhilRice News
PINOYRICE=false      # PinoyRice
OPENSTAT=false       # OpenSTAT (PSA)
IRRI=false           # IRRI News (Philippines)
```

Additional scraper settings (delays, headless mode, retry) are also controlled from `.env` (see comments in `src/scrapers/irri.py` and other scrapers).

### 2.2 Entry point

From project root:

```bash
python main.py
```

`main.py`:
- Reads `.env` flags to decide which source to run.
- For **PhilRice**, **PhilRice News**, and **IRRI** it runs both:
  1. Scraper (`src/scrapers/*`)
  2. Processing (`src/services/*`) to build the CPT corpus.

You can also re‑run processing alone when `.txt` files already exist:

```bash
python -m src.services.philrice
python -m src.services.philrice_news
python -m src.services.pinoyrice
python -m src.services.irri
```

---

## 3. Source‑specific Flows

### 3.1 PhilRice PDFs

- **Scraper**: `src/scrapers/philrice.py`
- **Raw outputs**:
  - `data/philrice/*.pdf`
  - `data/philrice/*.txt` (extracted text)
  - Checkpoint: `data/checkpoints/philrice_checkpoint.json`
- **Processing**: `src/services/philrice.py`
  - Input: `data/philrice/*.txt`
  - Outputs:
    - Corpus: `data/philrice_processed/philrice_corpus.jsonl`
    - Per file: `data/philrice_processed/per_file/*.json`

### 3.2 PhilRice News

- **Scraper**: `src/scrapers/philrice_news.py`
  - Crawls PhilRice news listing (with pagination) and saves article text as `.txt`.
- **Raw outputs**:
  - `data/philrice_news/*.txt`
  - Checkpoint: `data/checkpoints/philrice_news_checkpoint.json` (name may vary).
- **Processing**: `src/services/philrice_news.py`
  - Input: `data/philrice_news/*.txt`
  - Outputs:
    - Corpus: `philrice_news_processed/philrice_news_corpus.jsonl`
    - Per file: `philrice_news_processed/per_file/*.json`

### 3.3 PinoyRice

- **Scraper/processor**: `src/scrapers/pinoyrice.py` and `src/services/pinoyrice.py`
- **Outputs**:
  - Article corpus: `data/pinoyrice_processed/pinoyrice_corpus.jsonl`
  - PDFs corpus: `pinoyrice_processed/pinoyrice_pdfs_corpus.jsonl`
  - Additional structured files under `pinoyrice_processed/`.

### 3.4 IRRI News (Philippines)

- **Scraper**: `src/scrapers/irri.py`
  - Opens **All News** page.
  - Sets **Country** select to **Philippines** (`field_countries_ref_target_id = 18`).
  - Clicks **Search** (`button#edit-submit-related-news`).
  - For each listing page:
    - Collects all article cards (`/news-and-events/news/<slug>`).
    - For each card:
      - Navigates to the article.
      - Extracts the main body (no navigation, no “Related News” section).
      - Writes `.txt` file:
        - `data/irri_processed/text/<title>.txt`
        - Includes `URL:` and `Title:` header.
      - Downloads PDF links (if any) to `data/irri_pdfs/`.
      - Updates checkpoint (`data/checkpoints/irri_checkpoint.json`).
      - Returns to the listing page before clicking the next card.
    - Follows “Next page” until exhausted.

- **Processing**: `src/services/irri.py`
  - Input: `data/irri_processed/text/*.txt`
  - Cleaning:
    - Parses and removes `URL:` + `Title:` header.
    - Drops duplicate title line at the top of the body.
    - Strips leading date line (`Month DD, YYYY`) and `SHARE`.
    - Removes footer starting at `For more information, please contact`.
    - Normalizes whitespace while keeping paragraph breaks.
  - Outputs (same schema as PhilRice News):
    - Corpus: `data/irri_processed/irri_corpus.jsonl`
    - Per file: `data/irri_processed/per_file/*.json`

### 3.5 OpenSTAT (PSA)

- **Scraper**: `src/scrapers/openstat.py`
- **Outputs**:
  - Tables and structured data under `data/openstat/` (see scraper docstrings / comments).

---

## 4. CPT Record Schema

All text corpora use the same CPT record format, defined in `src/agri_corpus/cpt_utils.py`:

```json
{
  "text": "<cleaned body>",
  "input": "<same as text>",
  "content": "<same as text>",
  "source": "<philrice | philrice_news | pinoyrice | irri | ...>",
  "doc_id": "<stable identifier>",
  "filename": "<original .txt filename>"
}
```

Notes:
- `doc_id` is:
  - For PhilRice/IRRI/PhilRice News: a slug built from the cleaned article title.
  - For file‑based sources: derived from the `.txt` stem.
- If chunking is enabled (MAX\_CHUNK\_CHARS > 0), multiple records may share the same base `doc_id` with `_chunk_N` suffixes.

---

## 5. Where to Find Things

- **Scrapers**: `src/scrapers/*.py`
- **Services (cleaning + CPT)**: `src/services/*.py`
- **Text outputs**:
  - PhilRice PDFs: `data/philrice/*.txt`
  - PhilRice News: `data/philrice_news/*.txt`
  - IRRI News: `data/irri_processed/text/*.txt`
- **Final corpora**:
  - `data/philrice_processed/philrice_corpus.jsonl`
  - `philrice_news_processed/philrice_news_corpus.jsonl`
  - `data/pinoyrice_processed/pinoyrice_corpus.jsonl`
  - `pinoyrice_processed/pinoyrice_pdfs_corpus.jsonl`
  - `data/irri_processed/irri_corpus.jsonl`

