# Data sources – direct links (for data gathering → cleaning → ingestion)

*Use today for data gathering; clean today; ingest tomorrow.*

**Target (excluding Leeds):** ~10K–20K+ documents / 100M+ tokens for CPT; ~5K–10K SFT examples. Lahat ng nasa baba pwedeng kunin ngayon — wala dito ang Leeds data.

---

## Specifically: anong types ng data ang kukunin

| Type | Description | Use (CPT/SFT) | Saan kunin (examples) |
|------|-------------|----------------|------------------------|
| **1. Soil data** | Soil survey, fertility, nutrients, pH, fertilizer guide, province/municipality | CPT | BSWM soil survey reports, BSWM MAPS, Leeds (proprietary) |
| **2. Crop data** | Production, yield, area harvested, by crop (palay, corn, etc.), location, year | CPT | OpenSTAT, FAO FAOSTAT, FAO Microdata Crops Survey, Leeds |
| **3. Price data** | Farmgate/market prices by commodity, location, period (month/year) | CPT | OpenSTAT (may scraper ka na) |
| **4. Technical reports & publications** | DA/FAO/PhilRice/BAR reports, policy briefs, NAREA, R&D highlights | CPT | DA Publications, PhilRice downloads, BAR, FAO GIEWS |
| **5. Research papers** | Agri/rice/soil/pest/climate papers (Philippines, open access) | CPT | Google Scholar, SEARCA, AJAD, IRRI, AgEcon Search, Philippine Journal of Science, MDPI |
| **6. Field logs / extension data** | Real field notes, practices, Q&A from agriculturists/farmers | **SFT/RLHF** | 4 Agriculturists (NEP), FB farmer groups (with consent) |
| **7. Census/survey microdata** | Household/farm-level structure, crops, livestock (aggregated or request) | CPT | FAO Microdata (Crops Survey, Ag Census 2012) |
| **8. Knowledge products** | How-to guides, pest/disease ID, grain quality, soil ID | CPT | PhilRice Knowledge products, DA/BSWM guides |

**Short list (types to collect):**  
(1) Soil · (2) Crop production/yield · (3) Price · (4) Tech reports & publications · (5) Research papers · (6) Field logs (SFT) · (7) Census/survey data · (8) Knowledge products (guides).

*Leeds = soil + crop (1, 2) from their 1,000 ha. Lahat ng iba = open/supplementary sources above.*

---

## Link verification (checked 2026-03-10)

| Status | Meaning |
|--------|--------|
| OK | Reachable; use as-is. |
| 403 / timeout | May block automated requests; **try in your browser** — often works. |
| DOWN | Server error (e.g. 500/521); try again later or use alternative. |

**Verified OK:** FAO Data catalog, FAO Microdata (2385, 1639), FAO GIEWS Philippines, SEARCA Publications, SEARCA E-Library, AJAD, MDPI search, Google Scholar.  
**Try in browser (403/timeout from checker):** OpenSTAT, DA, PhilRice, BSWM, BAR, data.gov.ph, AgEcon Search, Philippine Journal of Science.  
**DOWN (use alternative):** FAO fenix bulk → use **FAO Data catalog** or **FAOSTAT web** (fao.org/faostat) for crop data.

---

## BULK / ONE-CLICK STYLE (madaming data agad)

| Source | Link | Status | Ano makuha |
|--------|------|--------|------------|
| **FAO bulk CSV (crop production, lahat bansa)** | https://fenixservices.fao.org/faostat/static/bulkdownloads/ | **DOWN** (500) — try later | ZIP: `crop_production_E_All_Data_(Normalized).zip` — filter Philippines sa CSV after download. |
| **FAO Data catalog – crop dataset** | https://data.apps.fao.org/catalog/dataset/crop-production-yield-harvested-area-global-national-annual-faostat | **OK** | Crop production, yield, area (1961–present); may download option. |
| **Open Data PH – DA datasets** | https://data.gov.ph/catalogue/dataset?organization=department-of-agriculture&tags=Agriculture | Try browser | List ng DA datasets (agriculture tag); i-download per dataset. |
| **PhilRice – Downloads (R&D, reports, mag)** | https://www.philrice.gov.ph/downloads/ | Try browser | R&D Highlights, PhilRice Magazine, Annual Reports, references. |
| **PhilRice – Knowledge products** | https://www.philrice.gov.ph/products/knowledge-products/ | Try browser | Field guides, soil ID, pest/disease, grain quality – PDFs. |
| **FAO Microdata – PH Crops Production Survey** | https://microdata.fao.org/index.php/catalog/2385 | **OK** | Philippines Crops Production Survey (282 crops, regional/provincial). |
| **FAO Microdata – PH Ag Census 2012** | https://microdata.fao.org/index.php/catalog/1639 | **OK** | Census of Agriculture and Fisheries 2012 – household/farm level. |

---

## 1. PSA OpenSTAT (agri price & production – may scraper ka na)

| What | Link |
|------|------|
| **OpenSTAT home** | https://openstat.psa.gov.ph/ |
| **Agriculture, Forestry, Fisheries** | https://openstat.psa.gov.ph/Database/Agriculture-Forestry-Fisheries |
| **Crops (palay, corn, etc.) – PX-Web** | https://openstat.psa.gov.ph/PXWeb/pxweb/en/DB/DB__2E__CS/?tablelist=true&rxid=bdf9d8da-96f1-4100-ae09-18cb3eaeb313 |
| **Livestock & poultry** | https://openstat.psa.gov.ph/PXWeb/pxweb/en/DB/DB__2E__LP__PDN/?tablelist=true&rxid=bdf9d8da-96f1-4100-ae09-18cb3eaeb313 |

---

## 2. Department of Agriculture (DA) – tech reports, publications

| What | Link |
|------|------|
| **DA home** | https://www.da.gov.ph/ |
| **DA Publications** | https://www.da.gov.ph/media-resources/publications/ |
| **DA Annual Reports** | https://www.da.gov.ph/media-resources/da-annual-reports/ |

---

## 3. DA attached agencies – soil, rice, research

| What | Link |
|------|------|
| **BSWM (Bureau of Soils and Water Management)** – soil surveys, maps | https://www.bswm.da.gov.ph/ |
| **BSWM Soil Survey Reports** (by province) | https://www.bswm.da.gov.ph/soil-survey-reportd/ |
| **BSWM MAPS** (soil fertility, fertilizer guide, nutrients) | https://www.bswm.da.gov.ph/bswm-maps/ |
| **BSWM Research & Development** | https://www.bswm.da.gov.ph/process/research-and-development/ |
| **PhilRice** (rice R&D, reports, PDFs) | https://www.philrice.gov.ph/ |
| **BAR (Bureau of Agricultural Research)** – BAR Digest, Chronicles, NAREA | https://bar.gov.ph/ |

---

## 4. FAO – global/Philippines agri data & reports

| What | Link |
|------|------|
| **FAO Philippines country brief (GIEWS)** | https://www.fao.org/giews/countrybrief/country.jsp?code=PHL |
| **FAOSTAT – Crops (production, yield, area)** | https://www.fao.org/faostat/en/#data/QCL |
| **FAO Data catalog – crop production dataset** | https://data.apps.fao.org/catalog/dataset/crop-production-yield-harvested-area-global-national-annual-faostat |
| **FAO Microdata – Philippines Crops Production Survey** | https://microdata.fao.org/index.php/catalog/2385 (catalog) · https://microdata.fao.org/index.php/catalog/study/PHL_CPS_2019_v01_EN_M_v01_A_OCS (2019 survey) |

---

## 5. Research papers – Google Scholar (maraming query = maraming papers)

| Search | Link |
|--------|------|
| Philippines agriculture | https://scholar.google.com/scholar?q=Philippines+agriculture |
| Philippines rice farmer | https://scholar.google.com/scholar?q=Philippines+rice+farmer |
| Philippines corn crop soil | https://scholar.google.com/scholar?q=Philippines+corn+crop+soil |
| Nueva Ecija agriculture | https://scholar.google.com/scholar?q=Nueva+Ecija+agriculture |
| Philippines DA FAO technical report | https://scholar.google.com/scholar?q=Philippines+DA+FAO+technical+report |
| Philippine rice production yield | https://scholar.google.com/scholar?q=Philippine+rice+production+yield |
| Philippines palay farming practices | https://scholar.google.com/scholar?q=Philippines+palay+farming+practices |
| Philippines soil fertility crop | https://scholar.google.com/scholar?q=Philippines+soil+fertility+crop |
| Philippines pest management rice | https://scholar.google.com/scholar?q=Philippines+pest+management+rice |
| Philippines irrigation agriculture | https://scholar.google.com/scholar?q=Philippines+irrigation+agriculture |
| Filipino farmers adaptation climate | https://scholar.google.com/scholar?q=Filipino+farmers+adaptation+climate |
| UPLB agriculture research Philippines | https://scholar.google.com/scholar?q=UPLB+agriculture+research+Philippines |
| PhilRice rice research | https://scholar.google.com/scholar?q=PhilRice+rice+research |
| BSWM soil survey Philippines | https://scholar.google.com/scholar?q=BSWM+soil+survey+Philippines |

*Tip: Sa Scholar, use "Since 2020" (or any year) left sidebar; click "PDF" / "All versions" to get downloadable PDFs; save lahat sa `papers_pdf` folder.*

---

## 5b. Research paper repositories (bulk open-access agri papers)

| Source | Link | Ano makuha |
|--------|------|------------|
| **SEARCA Publications** (filter Philippines) | https://www.searca.org/pubs | Proceedings, policy briefs, discussion papers, journals (1966–present). |
| **SEARCA E-Library** (~16,800 materials) | https://lis.searcaapps.org/lis/materials/precollection/ | Agriculture & rural development – search/filter then download. |
| **IRRI Publications** | https://www.irri.org/resources-and-tools/publications | Rice Today, annual reports, staff publications. |
| **Asian Journal of Agriculture and Development (AJAD)** | https://ajad.searca.org | Refereed journal – Philippines/Southeast Asia agri; many open PDFs. |
| **AgEcon Search – Philippines** | https://ageconsearch.umn.edu/search?q=Philippines+agriculture | Open-access ag econ papers; filter by Philippines, download PDF. |
| **Philippine Journal of Science** | https://philjournalsci.dost.gov.ph/ | DOST journal – agri/biology papers; open access. |
| **MDPI agriculture Philippines** | https://www.mdpi.com/search?q=Philippines+agriculture | Open access; search Philippines + agriculture. |

---

## 6. Facebook groups (actual farmer info)

Walang single “official” list; hanapin manually sa FB search. Suggested search terms:

- `Philippines farmers group`
- `Magsasaka Philippines`
- `Rice farmers Philippines` / `Palay farmers`
- `Nueva Ecija farmers`
- `Agricultural cooperatives Philippines`

*Tip: Join 1–2 groups, check group “Files” or “Guides”; kunin discussions/posts (with consent/terms); export or copy to text for cleaning. Pwede rin FB Group search: https://www.facebook.com/search/groups/?q=filipino%20farmers*

---

## Quick checklist (today = gather + clean) — lahat ito di kasama Leeds

- [ ] **Bulk:** FAO bulk download (fenix ZIP), Open Data PH DA, PhilRice downloads, FAO Microdata (Crops Survey + Ag Census)
- [ ] OpenSTAT – run scraper / manual download (may `scraper.py` ka na)
- [ ] DA Publications + Annual Reports – download PDFs/reports
- [ ] BSWM – soil survey reports (pick provinces, e.g. Nueva Ecija)
- [ ] PhilRice – technical reports, R&D highlights, Knowledge products (PDF)
- [ ] BAR – BAR Digest, Chronicles, NAREA (PDF)
- [ ] FAO – country brief, FAOSTAT Philippines crop data (CSV/Excel)
- [ ] **Google Scholar** – use all 14 search links above; save PDFs to one folder
- [ ] **Repositories** – SEARCA, IRRI, AgEcon Search, Philippine Journal of Science, AJAD, MDPI
- [ ] FB groups – list groups + plan how to capture text (manual or tool; respect ToS)

*Suggestion: Create folders `da_reports`, `bswm_soil`, `philrice_pdfs`, `fao_data`, `papers_pdf`, `fb_captures` so bukas ingestion = per-source pipeline na lang. Target: 10K–20K+ docs (100M+ tokens) from these sources for CPT.*
