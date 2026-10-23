# Data format spec – LLM / NEP (Sovereign AgriLLM)

Para clear sa lahat: anong format ng output natin at bakit.

---

## Verification checklist (bago i-handoff)

- [ ] **Run validator:** `python validate_philrice_jsonl.py philrice_processed/philrice_corpus.jsonl` → dapat "OK – Format valid".
- [ ] **Required keys:** Bawat line may `text`, `input`, `content` (lahat same value).
- [ ] **Hindi Alpaca:** Walang `instruction`/`output` – CPT (raw text) lang.
- [ ] **Encoding:** File ay UTF-8 (ok for Tagalog/special chars).
- [ ] **NEP alignment:** Data ay for **CPT** (continued pre-training); SFT/field logs ay separate format.

---

## PhilRice (at iba pang CPT sources) – `philrice_corpus.jsonl`

**Use:** Continued pre-training (CPT). **Hindi** Alpaca. **Hindi** instruction format.

**Format:** JSONL (one JSON object per line).

**Schema per line:**

| Field     | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `text`    | string | ✅       | Raw text chunk. HuggingFace, LLaMA-Factory, most CPT. |
| `input`   | string | ✅       | Same as `text`. AWS Bedrock CPT, etc. |
| `content` | string | ✅       | Same as `text`. Some pipelines expect `content`. |
| `source`  | string | optional | e.g. `"philrice"`. |
| `doc_id`  | string | optional | Unique id (e.g. `filename_page_1`). |
| `filename`| string | optional | Original PDF filename. |
| `page`    | int    | optional | Page number. |

**Example line:**
```json
{"text": "Rice production in the Philippines...", "input": "Rice production in the Philippines...", "source": "philrice", "doc_id": "report_page_1", "filename": "report.pdf", "page": 1}
```

**Compatible with:**
- CPT (continued pre-training) pipelines na expect `text` or `input`.
- Hindi para sa instruction/SFT; kung SFT (e.g. field logs) ang gagawin, ibang format (e.g. Alpaca) ang kailangan – separate pipeline.

---

## OpenSTAT (agri price) – CSV / MySQL

Handled by `processing.py` and `database.py`. Tabular data; kung kailangan as text for CPT, dapat i-convert to sentences/paragraphs in a separate step (not covered here).

---

## Summary

| Data           | Format | Use  | Alpaca? |
|----------------|--------|------|---------|
| PhilRice etc.  | JSONL (`text` + `input`) | CPT | No |
| Field logs (future) | TBD (e.g. Alpaca) | SFT | Maybe |

**Validate bago i-handoff:**  
`python validate_philrice_jsonl.py philrice_processed/philrice_corpus.jsonl`  
– chine-check na valid JSON per line, may `text`/`input`/`content`, at `text == input`.

**Kung may nagtanong:** “CPT data natin JSONL, may `text`, `input`, `content` (same value), one document per line. Compatible sa standard CPT pipelines. Hindi Alpaca.”
