# IRRI Philippines – Link check report

**Source list:** `irri_philippines_COMPLETE.md`  
**Checked:** Sample of links per section (manual fetch). Use this **before** building any IRRI scraper/processor.

---

## Summary

| Section | Sample checked | Status | Notes |
|--------|----------------|--------|--------|
| 1 – Main PH pages | 4/4 | OK | All return 200, HTML content |
| 2 – News articles | 4 | OK | Standard + `%E2%80%99` path work |
| 3 – Projects | 4 | OK | `/node/2127`, `/node/2132`, `/node/2129` + project slugs |
| 4 – Digital tools | 2 | Mixed | Hub OK; AutoMonPH timeout; DA sites need browser |
| 5 – Policy briefs | 2/2 | OK | hdl.handle.net + PDF download links |
| 6–8 – Resources / Institutional | 3 | OK | who-we-are, news?country=Philippines |

---

## Section 1 — Main Philippines pages

| # | URL | Status |
|---|-----|--------|
| 1 | https://www.irri.org/where-we-work/philippines | OK – full content |
| 2 | https://www.irri.org/where-we-work/southeast-asia | OK |
| 3 | https://www.irri.org/where-we-work | OK |
| 4 | https://www.irri.org/news-and-events/experience-irri | OK |

---

## Section 2 — News articles

**Base:** `https://www.irri.org` + path.

- **Checked:**  
  - `/news-and-events/news/whats-next-climate` → OK  
  - `/news-and-events/news/when-science-meets-policy-quezon-city-turns-vendor-business-school-pilot` → OK  
  - `/news-and-events/news/low-gi-rice-seen-promising-solution-mitigate-asia%E2%80%99s-diabetes-crisis` → OK (encoded apostrophe)
- **Listing page:** `https://www.irri.org/news-and-events/news?country=Philippines` → OK (filter may be JS-rendered; listing still loads).
- **Assumption:** Other news paths in the doc (same pattern `/news-and-events/news/<slug>`) will work unless slug is wrong or removed. Recommend spot-check a few more before full crawl.

---

## Section 3 — Projects

| # | URL | Status |
|---|-----|--------|
| 1 | https://www.irri.org/node/2127 (Evolving Philippine Rice Economy) | OK |
| 2 | https://www.irri.org/node/2132 (ASEAN-CGIAR) | OK |
| 3 | https://www.irri.org/projects/accelerating-scaling-low-emissions-rice-southeast-asia-acceler | OK (checked earlier) |
| 4 | https://www.irri.org/projects/reducing-methane-emissions-rice-remet-rice-project | OK (checked earlier) |
| 5 | https://www.irri.org/node/2129 (PlantDirect) | OK |
| 6 | https://www.irri.org/node/2133 | Not fetched – same domain, expect OK |

---

## Section 4 — Digital tools (Philippines-related)

| # | URL | Status | Note |
|---|-----|--------|------|
| 1 | https://www.irri.org/automonph | Timeout | Page may be heavy or slow; try with longer timeout or browser |
| 2 | https://pestrisk.buplant.da.gov.ph/tools/ | Not fetched | DA/BPI site – often 403 for bots; use browser or Playwright |
| 3 | PRISM (listed on hub only) | – | No direct PRISM URL in list; hub lists it |
| 4 | https://rcm.da.gov.ph/home | 403 (from earlier check) | Use browser / Playwright |
| 5 | https://www.irri.org/easyharvest | Not fetched | Same domain – likely OK |
| 6 | https://www.irri.org/resources-and-services/digital-innovations | OK | Hub page; lists AutoMonPH, PRISM, RCMAS, PRIME, etc. |
| 7–11 | Sub-categories (information-dissemination, service-delivery, etc.) | Not fetched | Same domain – likely OK |

---

## Section 5 — Policy briefs (hdl.handle.net)

| # | URL | Status | Note |
|---|-----|--------|------|
| 1 | https://hdl.handle.net/10568/178149 (Philippine Rice Policy) | OK | Metadata + PDF link (cgspace.cgiar.org bitstream + books.irri.org) |
| 2 | https://hdl.handle.net/10568/177973 (PH, Thailand, Vietnam) | OK | Metadata + PDF link (cgspace bitstream) |

**Scraper note:** For PDFs, use the “External link to download” or bitstream link from the hdl page (e.g. `http://books.irri.org/briefs/...` or cgspace.cgiar.org bitstream).

---

## Section 6–8 — Resources, people, institutional

- **Policy briefs hub:** https://www.irri.org/resources-and-services/policy-briefs-and-white-papers – not fetched; same domain.
- **Digital innovations:** OK (see Section 4).
- **Who we are:** https://www.irri.org/who-we-are → OK.
- **News filter:** https://www.irri.org/news-and-events/news?country=Philippines → OK.
- **Jobs/careers:** https://www.irri.org/jobs – not fetched; same domain.

---

## Recommendations before building scraper/processor

1. **irri.org** – Safe to scrape with `requests` or Playwright for:
   - Where we work (PH, SEA, overview)
   - News listing and article URLs from the doc
   - Project pages (`/node/2127`, `/node/2132`, etc., and `/projects/...`)
   - Digital innovations hub and sub-pages
   - Policy briefs hub
   - Who we are, leadership, etc.
2. **AutoMonPH** (`/automonph`) – Use longer timeout or Playwright; page may be app-like/slow.
3. **DA/BPI (rcm.da.gov.ph, pestrisk.buplant.da.gov.ph)** – Expect 403 for plain HTTP; use Playwright (or browser) and same pattern as PhilRice/OpenSTAT.
4. **hdl.handle.net** – Works for metadata + PDF links; follow “download” links to actual PDF (cgspace or books.irri.org).
5. **News pagination** – Doc says `?page=0,1,2...`; confirm in browser or one test fetch.
6. **robots.txt** – Check `https://www.irri.org/robots.txt` before large-scale crawl.

---

*Report generated from spot-checks; not every URL in irri_philippines_COMPLETE.md was fetched. Re-run checks before production scrape.*
