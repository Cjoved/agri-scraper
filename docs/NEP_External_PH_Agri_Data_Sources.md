# NEP — External / Local (PH) Agri Data Sources for Fine-Tuning

**Purpose:** Mga **external, local (Philippines only)** na source ng agri data — **lahat lahat**: research papers, theses, journals, Excel/datasets, **Google Scholar**, at iba pang research documents na related sa agriculture sa Pilipinas — para sa fine-tuning. **Walang images** sa list na ito; text/tabular/PDF/Excel lang.

---

## 1. Official statistics (Excel / tabular)

| Source | Link | Ano makukuha |
|--------|------|----------------|
| **PSA OpenSTAT — Crops (main)** | https://openstat.psa.gov.ph/ | Homepage. Pili: **Database** → Agriculture, Forestry, Fisheries → **Crops**. May export to **Excel**. |
| **PSA OpenSTAT — Crop tables (PX-Web)** | https://openstat.psa.gov.ph/PXWeb/pxweb/en/DB/DB__2E__CS/?tablelist=true&rxid=bdf9d8da-96f1-4100-ae09-18cb3eaeb313 | Direct to crop tables: Palay/Corn volume, area harvested, other crops (345+), stocks. Select variables → export **Excel**. |
| **PSA OpenSTAT — User's Guide** | https://openstat.psa.gov.ph/Database/Users-Guide | Paano gamitin at i-download data. |
| **PSA Region III — Nueva Ecija** | https://rsso03.psa.gov.ph/nueva-ecija | Region 3 (includes Nueva Ecija) — reports, stats. May link to **Crops Production in Nueva Ecija** (e.g. 2022–2023). |
| **PSA RSO III — Crops Production NE 2022–2023** | https://rsso03.psa.gov.ph/content/crops-production-nueva-ecija-2022-2023 | Nueva Ecija crop production (volume, etc.) — text/tabular. |

*Note: OpenSTAT may need browser; kung may scraper (e.g. Agri-Scraper), puwede i-automate ang pag-download ng Excel.*

---

## 2. Soil & rice data (PhilRice — DA)

| Source | Link | Ano makukuha |
|--------|------|----------------|
| **PhilRice — Philippine soils (overview)** | https://www.philrice.gov.ph/philippine-soils-online-data-treasury/ | Intro sa soil data; link to DBMP. ~400 Soil Series, properties, guidebooks. |
| **PhilRice DBMP (Database portal)** | https://dbmp.philrice.gov.ph/dbmp_main | Main portal: soil info, **PalayStat** (rice farm household survey), seed varieties, pest info, GIS. |
| **PhilRice DBMP — PalayStat** | https://dbmp.philrice.gov.ph/dbmp_main/palaystat | Rice-Based Farm Household Survey (RBFHS) data — tabular. |
| **PhilRice DBMP — Soil Series** | https://dbmp.philrice.gov.ph/soils | Soil series data (physical/chemical) — text/tabular. |
| **PhilRice DBMP — FAQs (Rice)** | https://dbmp.philrice.gov.ph/FAQs | Rice production FAQs — text; useful for Q&A / instruction tuning. |

---

## 3. Research papers & manuals (PDF, text)

| Source | Link | Ano makukuha |
|--------|------|----------------|
| **PhilRice — Rice Breeding Manual (2023)** | https://www.philrice.gov.ph/wp-content/uploads/2023/05/Rice-Breeding-Manual_May-2023.pdf | PDF: breeding, pest/disease, grain quality — good for domain text. |
| **PhilRice — Competitiveness of Philippine Rice (2016)** | https://www.philrice.gov.ph/wp-content/uploads/2016/08/Book_CPRA_22June2016_3.pdf | PDF: benchmarking, methods — PhilRice + IRRI. |
| **Central Luzon Loop Survey (Springer)** | https://link.springer.com/chapter/10.1007/978-981-19-5542-6_3 | Research: rice farming PH 1966–2021 (IRRI). May paywall; abstract/chapter info for citations. |
| **IRRI — Rice varieties / trials (PLOS ONE)** | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0164456 | Open-access: multi-environment trials, crop modeling — dataset/methods in text. |
| **IRRI — Elite core panel (The Rice Journal, open)** | https://thericejournal.springeropen.com/articles/10.1186/s12284-021-00533-5 | Open-access: breeding lines, irrigated rice PH — text + data description. |

---

## 3A. Google Scholar — agriculture Philippines (lahat related research)

**Link:** https://scholar.google.com/

**Suggested search queries (i-copy-paste or i-adapt):**

| Query | Para saan |
|--------|-----------|
| `agriculture Philippines` | General PH agri research |
| `rice production Philippines` | Palay, rice farming |
| `crop production Philippines` | Crops, yield, area |
| `soil Philippines agriculture` | Soil, fertility, management |
| `Nueva Ecija agriculture` | Pilot area–specific |
| `organic farming Philippines` | Organic, sustainable |
| `PhilRice` | PhilRice papers |
| `IRRI Philippines` | IRRI studies in PH |
| `UPLB agriculture` | UPLB/CAFS research |
| `palay corn Philippines` | Major commodities |
| `agricultural extension Philippines` | Extension, farmers |
| `postharvest Philippines` | Postharvest, storage |
| `pest management rice Philippines` | Pest, disease |
| `fertilizer rice Philippines` | Fertilizer use |
| `site:philjournalsci.dost.gov.ph agriculture` | DOST Philippine Journal of Science only |
| `site:ukdr.uplb.edu.ph agriculture` | UPLB repository only |
| `site:philrice.gov.ph` | PhilRice site only |

*Tip: Sa Google Scholar, filter by year (e.g. Since 2020) o “Sort by relevance.” Puwede rin `filetype:pdf` kung PDF lang gusto mo. Lahat ng hits na related sa agriculture dito sa Pilipinas — papers, theses, reports — pwede i-collate para sa fine-tuning.*

---

## 4. PH peer-reviewed journals (research papers, PDF)

| Source | Link | Ano makukuha |
|--------|------|----------------|
| **Philippine Journal of Science (DOST)** | https://philjournalsci.dost.gov.ph/ | Peer-reviewed; rice, crops, pest, soil, breeding, postharvest — maraming agri articles. May PDF. |
| **PJS — Sample agri articles** | https://philjournalsci.dost.gov.ph/agronomic-yield-and-yield-related-traits-of-lowland-rice-oryza-sativa-l-to-the-regeneration-plasticity-of-ratoon-crop/ | Example: lowland rice, ratoon. |
| **PJS — Rice stem borer, germplasm** | https://philjournalsci.dost.gov.ph/135-vol-153-no-6a-december-2024-part-a/2219-evaluation-of-selected-philippine-germplasm-for-resistance-to-rice-stem-borer-scirpophaga-spp-using-seven-morphological-traits | Rice resistance, PH germplasm. |
| **PJS — Direct-seeded rice** | https://philjournalsci.dost.gov.ph/adoption-and-performance-of-direct-seeded-rice-dsr-technology-in-the-philippines/ | DSR technology PH. |
| **The Philippine Agricultural Scientist (UPLB)** | https://www.ukdr.uplb.edu.ph/pas/ | Int’l journal tropical agriculture; crop, animal, soil, horticulture, ag econ. Since 1911. |
| **PAS — About & access** | https://www.ukdr.uplb.edu.ph/pas/about.html | Scope, indexing. |
| **PAS — Most popular papers** | https://www.ukdr.uplb.edu.ph/pas/topdownloads.html | Top-downloaded articles. |
| **PAS — OVCRE journal portal** | https://ovcre.uplb.edu.ph/journals-uplb/index.php/PAS/index | Alternative access. |

---

## 5. University theses & repositories (theses, dissertations)

| Source | Link | Ano makukuha |
|--------|------|----------------|
| **UPLB — Theses & Dissertations (main)** | https://www.ukdr.uplb.edu.ph/etd/ | Lahat ng ETD sa UPLB. |
| **UPLB — College of Agriculture and Food Science (CAFS)** | https://www.ukdr.uplb.edu.ph/cafs/ | Crop science, animal science, food science, weed science, plant pathology, etc. |
| **UPLB CAFS — Undergraduate theses** | https://www.ukdr.uplb.edu.ph/cafs-etd-undergrad/index.16.html | Undergrad theses (e.g. since 1989). |
| **UPLB — College of Arts and Sciences (CAS) undergrad theses** | https://www.ukdr.uplb.edu.ph/cas-etd-undergrad/index.12.html | CAS theses (may agri-related). |
| **UPLB — Best theses/dissertations (CAFS)** | https://www.ukdr.uplb.edu.ph/exhibit/best-theses-and-dissertations/college-of-agriculture-and-food-science-cafs/ | Sample of best CAFS outputs. |

*UKDR = University Knowledge Digital Repository. Search by keyword: rice, crop, soil, Nueva Ecija, etc.*

---

## 6. DA publications & AgriLib

| Source | Link | Ano makukuha |
|--------|------|----------------|
| **DA — Publications (official)** | https://www.da.gov.ph/media-resources/publications/ | AFID, BAR, BPI, BSWM, ACPC — reports, guides, climate, commodities. |
| **DA — Download** | https://www.da.gov.ph/download/ | Downloadable materials. |
| **AgriLib (DA digital library)** | https://repository.upou.edu.ph/ (search AgriLib / DA) | Bibliographic search, digitized DA publications. |
| **NFRDI Library (DA)** | https://library.nfrdi.da.gov.ph/cgi-bin/koha/opac-search.pl | Searchable catalog; fisheries/agri. |

---

## 7. SEARCA (Southeast Asia, HQ Philippines)

| Source | Link | Ano makukuha |
|--------|------|----------------|
| **SEARCA — Home** | https://www.searca.org/ | Regional agri research; PH-based. |
| **SEARCA — Publications** | https://www.searca.org/pubs | Proceedings, discussion papers, policy briefs, theses abstracts, books, journals (e.g. AJAD, SABRAO). |
| **SEARCA — E-Library** | https://lis.searcaapps.org/ | Searchable repository; 3,900+ books; theses, journals — sustainable agri, crops, organic, rural dev’t. |
| **SEARCA — Knowledge Platform** | https://knowledgeplatform.searca.org/knowledge-resources/ | Knowledge products, digital tools. |
| **SEARCA — Research** | https://www.searca.org/research | Research program; food security, climate, farmer income. |

---

## 8. Bureau of Agricultural Research (DA-BAR)

| Source | Link | Ano makukuha |
|--------|------|----------------|
| **BAR — Home** | https://bar.gov.ph/ | Annual reports, digests, chronicles, featured tech, e-newsletters — downloadable materials (often PDF). |
| **FOI — BAR information documents** | https://foi.gov.ph/agencies/bar/information-documents | Request or browse BAR documents/datasets via FOI. |

---

## 9. IRRI (headquarters sa PH — Los Baños)

| Source | Link | Ano makukuha |
|--------|------|----------------|
| **IRRI — Resources** | https://www.irri.org/resources | Central page: publications, data tools, links to datasets. |
| **IRRI — Farm Household Survey Database** | https://sites.google.com/irri.org/fhsd2/home | Farm-level data: productivity, inputs, prices, income — Asia (incl. PH). For research; may request/access policy. |
| **IRIC — Data and Analysis Portal** | https://iric.irri.org/resources/iric-data-and-analysis-portal | Rice data and analysis tools. |
| **IRRI — Golden Rice Dataverse (Harvard)** | https://dataverse.harvard.edu/dataverse/goldenrice | Datasets (IRRI/PhilRice related); may registration. |

---

## 10. FOI (formal data request — PH gov’t)

| Source | Link | Ano makukuha |
|--------|------|----------------|
| **FOI — Agricultural data PH (PSA)** | https://foi.gov.ph/requests/agricultural-data-in-the-philippines-1960-2019-psa-530455091882 | Example request for agri data 1960–2019. Puwede mag-request ng bulk/Excel. |
| **FOI — DA agricultural production Nueva Ecija** | https://foi.gov.ph/requests/agricultural-production-report-of-nueva-ecija | Request production reports for Nueva Ecija. |
| **FOI — DA high-valued produce NE** | https://foi.gov.ph/agencies/da/2023-high-valued-produced-report-in-nueva-ecija | Example: 2023 high-value crops report NE. |

---

## 11. Quick summary — “Saan ako kukuha ng external PH data para sa fine-tuning?”

- **Excel / tabular:** PSA OpenSTAT (crops, palay/corn, by region/province), PhilRice DBMP (PalayStat, soil series), PSA RSO III (Nueva Ecija).
- **Google Scholar:** Gamitin ang suggested queries sa Section 3A (e.g. `agriculture Philippines`, `rice production Philippines`, `site:philjournalsci.dost.gov.ph`) — **lahat** related agri research dito sa PH.
- **Research / journals (PDF):** Philippine Journal of Science (DOST), The Philippine Agricultural Scientist (UPLB), PhilRice manuals, IRRI/Springer/PLOS papers (Section 3, 4).
- **Theses & repos:** UPLB UKDR (CAFS, CAS theses), SEARCA e-library, DA publications, AgriLib (Section 5, 6, 7).
- **Request-based:** BAR (bar.gov.ph), FOI (PSA, DA) kung kailangan ng specific bulk or reports (Section 8, 10).

*Lahat dito ay **local (PH)** o **PH-based** (IRRI, SEARCA HQ sa Philippines). **Walang image datasets** na included; focus ay text, tables, Excel, PDF.*

---

*For NEP fine-tuning: i-prioritize OpenSTAT + PhilRice DBMP/PalayStat + PhilRice/IRRI PDFs + Google Scholar + PJS/PAS + UPLB/SEARCA para **lahat lahat** na agri research documents dito sa Pilipinas.*
