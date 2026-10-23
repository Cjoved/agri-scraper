# Analysis: biotech.buplant.da.gov.ph (before building scraper_biotech)

**Link:** https://biotech.buplant.da.gov.ph/  
**Purpose:** Analyze the whole website before writing scraper code.

---

## 1. What we know (from search & DA context)

- **Owner:** Bureau of Plant Industry (BPI), Department of Agriculture (DA), Philippines.
- **Subdomain:** `biotech.buplant.da.gov.ph` — likely the **biotechnology** section of BPI (main site: buplant.da.gov.ph).
- **Mandate:** Biotechnology regulation and plant industry; Joint Department Circular No. 1, s. 2016 (R&D, handling, transboundary movement, release of GMO plants, etc.).
- **Relevance for NEP/agri data:** BPI handles seeds, plant variety registration, plant genetic resources, quarantine, crop R&D — good source of regulatory and technical text/PDFs for training data.

---

## 2. Technical note (403 on fetch)

- Direct HTTP fetch (e.g. `requests` or simple `fetch`) to the URL returns **403 Forbidden**.
- Same for `buplant.da.gov.ph` root — suggests bot/script blocking; **browser-based access (Playwright)** will be needed for scraping, same as PhilRice.

---

## 3. Expected site structure (to verify when we run Playwright)

Typical DA/BPI-style sites have:

- **Home** — landing, links to main sections.
- **About / Mandates** — text pages (mandate, history, org).
- **Divisions / Units** — e.g. CRPSD (Crop Research and Production Support Division), biotech unit.
- **Publications / Downloads / Resources** — **primary target for PDFs** (reports, circulars, guidelines).
- **Laws & Issuances** — JDC, circulars (often PDF).
- **Contact / FAQ** — less important for corpus.

For **biotech.buplant.da.gov.ph** specifically, we should look for:

- Main nav (top/side): Home, About, Mandates, Publications, Downloads, Links, Contact, etc.
- **Dropdowns or sub-menus** under each (like PhilRice Downloads).
- **List pages** with links to PDFs or “Read/Download” buttons.
- **Pagination** (page/2/, page/3/) or “Next”/“Last” if many items.
- **Direct PDF links** (.pdf or download handler URLs).

---

## 4. What to scrape (goals)

- **PDFs:** All downloadable documents (reports, circulars, guidelines, forms, issuances) — same idea as PhilRice: “lahat ng PDF na makukuha.”
- **Key pages:** At least: Home, any “Downloads” or “Publications” or “Resources” section, and every sub-section under them (per “button”/dropdown).
- **Text pages (optional):** If we also want clean text from non-PDF pages (e.g. mandate, history), we can add a second pass; for now **focus = PDF discovery and download**.

---

## 5. Suggested approach for scraper_biotech (after analysis)

1. **Launch browser (Playwright)** — same stack as PhilRice to avoid 403.
2. **Visit homepage** — get full DOM, parse all `<a href>` for same-domain links.
3. **Identify “main” sections** — especially links containing “download”, “publication”, “resource”, “circular”, “issuance”, “form”, etc.
4. **Visit each main section** — then for each section, collect sub-links (dropdown/sub-pages) and visit those too (same “main then sub” order as PhilRice).
5. **On every page:** collect links that point to PDFs (`.pdf`, or download handler patterns); optionally collect “Read”/“Download” buttons that resolve to PDFs.
6. **Pagination:** On list pages, follow “Next” or `page/2/`, `page/3/`, etc., and collect PDFs from each page.
7. **Download:** Same pattern as PhilRice — e.g. per-section or batch, with checkpoint (so we don’t re-download), save to a folder like `biotech_pdfs/`.
8. **Checkpoint & resume:** Save `biotech_checkpoint.json` with `downloaded_urls` so we can resume and skip already-downloaded files.

---

## 6. Next steps (when you’re ready to code)

1. Run a **one-off Playwright script** (or manual run) to:
   - Open https://biotech.buplant.da.gov.ph/
   - Dump the list of all internal links (and optionally their link text) from the main nav and footer.
   - Note which links lead to “list” pages (many links per page) vs single document.
2. **Map structure:** Write down main menu labels and their sub-items (e.g. “Downloads” → [“Circulars”, “Forms”, “Reports”]).
3. **Implement scraper_biotech.py** using the same patterns as scraper_philrice (main page first, then sub-pages, collect PDFs, pagination, checkpoint, download to `biotech_pdfs/`).
4. **Processing:** Reuse or adapt processing_philrice logic to convert `biotech_pdfs/` to JSONL/CPT (e.g. `processing_biotech.py` or one shared processor with a source flag).

---

## 7. Summary

| Item | Conclusion |
|------|------------|
| **Site** | biotech.buplant.da.gov.ph — BPI/DA biotechnology section. |
| **Access** | 403 on simple fetch → use **Playwright** for scraping. |
| **Content to scrape** | All PDFs from the site (publications, downloads, resources, circulars, etc.). |
| **Order** | Main page first, then all relevant sub-sections/dropdowns (per button). |
| **Scraper name** | `scraper_biotech.py`; output e.g. `biotech_pdfs/`, `biotech_checkpoint.json`. |

No scraper code has been written yet; this file is analysis and plan only. Once you’ve confirmed or adjusted this (e.g. after a quick manual look at the site), we can implement `scraper_biotech.py` accordingly.
