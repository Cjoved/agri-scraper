# NEP Technical Requirements — Data Requirements Collation

**Source:** NEP _ Technical Requirements Document.docx  
**Project:** Sovereign AI for Filipino Farmers (Nueva Ecija Pilot)  
**Purpose:** I-collate lahat ng data requirements at linawin **saan kukunin ang agri data**.

---

## 1. Data requirements (lahat na nabanggit sa TRD)

| # | Data requirement | Purpose | **Source (saan kukunin)** |
|---|------------------|--------|---------------------------|
| 1 | **Leeds' 1,000-ha soil/crop data** | Continued Pre-training (CPT) sa Red Dragon node | **Leeds (Jofer/Leeds)** — proprietary dataset nila; *hindi public, sila ang magpro-provide* |
| 2 | **Field logs from the 4 Agriculturists** | RLHF/SFT — fine-tune ng model (Farmer-LLM-8B) | **4 Agriculturists** — galing sa field work nila; *kailangan i-define ang protocol (e.g. Digital Shaman 7-step) para sa collection* |

Walang ibang explicit “agri data” source na binanggit sa TRD (walang PSA, BAS, DA, or public URL/API).

---

## 2. Saan talaga kukunin ang agri data? (Summary)

Sa TRD, **dalawang source lang** ng agri data ang nakalagay:

1. **Leeds (1,000-ha soil/crop data)**  
   - **Saan:** Galing sa **Leeds** (stakeholder: Jofer/Leeds — Infrastructure/Pilot).  
   - **Ano:** Proprietary soil/crop data for 1,000 hectares.  
   - **Para kanino:** Dr. Cedric Festin ang mag-i-ingest (Day 16–45) para sa unang “Agri-8B-v1” GGUF.  
   - **Action:** Kailangan i-request/coordinate sa **Leeds/Jofer** ang delivery ng dataset (format, schema, NDA kung proprietary).

2. **4 Agriculturists (field logs)**  
   - **Saan:** Galing sa **4 Agriculturists** sa field.  
   - **Ano:** Field logs na gagamitin para sa RLHF/SFT.  
   - **Para kanino:** Dr. Cedric (fine-tuning pipeline); Reuben (Field Protocols — “Digital Shaman” 7-step manual).  
   - **Action:** I-define ang **field protocol** at **data template** (what to log, format, how often) para consistent ang collection.

So: **hindi binabanggit sa TRD ang PSA, BAS, or ibang public website bilang source ng agri data.** Ang agri data ay internal/proprietary (Leeds) at field-collected (4 Agriculturists).

---

## 3. Technical stack (san gagamitin ang data)

| Component | Role | Data used |
|-----------|------|-----------|
| **Red Dragon (H20)** | Training & management | Leeds 1,000-ha data (CPT) + field logs (RLHF/SFT) |
| **Agri-8B-v1 (GGUF)** | Edge model | Output ng training sa above data |
| **Urovo PDAs (104 devices)** | Edge UI (100 farmers) | Offline inference; *no direct “data source” — model na ang naka-deploy* |

---

## 4. Suggested next steps (para ma-prepare lahat ng data)

1. **Leeds dataset**  
   - Confirm kay **Leeds/Jofer**: format (e.g. CSV/DB/API), schema (soil vars, crop vars, location, dates), coverage (1,000 ha), at timeline of delivery.  
   - Document: file naming, versioning, at kung may NDA/restrictions.

2. **Field logs (4 Agriculturists)**  
   - With **Reuben**: finalize “Digital Shaman” 7-step manual at **data dictionary** (fields to log, units, codes).  
   - Define: storage (where to submit logs), frequency (per crop cycle / per week), at QC (who validates).

3. **Optional — open data (wala sa TRD)**  
   - Kung gusto niyo mag-add ng **public agri data** (e.g. PSA, BAS, DA, OpenStat), puwede i-list as *additional* sources for future phases; current TRD Phase 1 explicitly relies only on **Leeds + field logs**.
   - **Listahan ng external/local (PH) sources** para sa fine-tuning (research papers, Excel, PSA, PhilRice, IRRI, etc.): see **`NEP_External_PH_Agri_Data_Sources.md`**.

---

## 5. One-line answer

**“Alin dito yung pagkukuhanan ko ng agri data?”**  
Sa NEP TRD: **(1) Leeds** — 1,000-ha soil/crop data (proprietary), at **(2) 4 Agriculturists** — field logs. Walang public URL/API na specified; kailangan i-coordinate sa Leeds at i-define ang protocol para sa agriculturists.

---

*Generated from NEP _ Technical Requirements Document.docx.*
