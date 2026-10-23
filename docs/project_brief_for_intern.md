# Project context for data curation (intern-safe)

**Use this when the intern asks for project details. Do not share the full NEP/technical requirements doc.**

---

## What we're building

We're preparing data for an **agriculture-focused LLM** that will support Filipino farmers. The model will be used in the field (offline-capable, farmer-facing). This is a pilot with academic and industry partners.

---

## Why data curation matters

The model will be trained in two stages:

1. **Continued pre-training (CPT)**  
   Large volumes of agriculture-related text (reports, manuals, surveys, crop/soil data) so the model learns domain language and facts.

2. **Fine-tuning (SFT)**  
   Curated examples (e.g. Q&A, instructions, field scenarios) so the model responds in a useful, consistent way for farmers and extension workers.

Our job is to **curate and clean** data for both stages: find sources, clean text, and format for training. We do **not** handle the actual training runs or infrastructure.

---

## What “good” data looks like

- **Topic:** Philippine agriculture — crops (e.g. palay, corn), soil, pests, diseases, practices, climate, prices, surveys.
- **Language:** Filipino/Tagalog preferred where possible; English from official sources (DA, PhilRice, FAO, etc.) is also useful.
- **Formats:** Plain text, structured tables (CSV), PDFs we can extract text from. Clean, machine-readable.
- **Rough scale (for planning):** On the order of tens of thousands of documents or equivalent for CPT, and thousands of high-quality examples for SFT. Exact targets are set by the training team.

---

## Your role as intern

- **Sourcing:** Use the data sources list (e.g. OpenSTAT, DA, PhilRice, FAO, SEARCA) to identify and collect datasets or documents.
- **Cleaning:** Remove junk, fix encoding, normalize structure so the training pipeline can ingest the data.
- **Formatting:** Help structure data into the formats required for CPT (e.g. long text chunks) and SFT (e.g. instruction–response pairs), as specified by the project lead.
- **Documentation:** Note what you downloaded, from where, and any issues (e.g. broken links, missing fields) so we can track progress and quality.

You will **not** need access to confidential project docs, hardware specs, or partner names. This brief plus the data sources list and any task-specific instructions from Crich are enough to do the curation work.

---

## What to ask Crich

- Which source or data type to prioritize.
- Exact format/template for SFT examples once the training team defines it.
- Where to save outputs (folders, naming, versioning).
- Any new sources to add or domains to focus on.

---

*This brief is approved for sharing with the intern. Do not attach or reference the full NEP/technical requirements document.*
