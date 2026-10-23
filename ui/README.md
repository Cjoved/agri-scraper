# OpenStatv2 Streamlit UI

Optional dashboard to **run one scraper** and watch **live terminal-style output** (same as `python main.py`), plus a checklist of expected output files.

## Setup

From the project root, with your venv activated:

```bash
pip install -r ui/requirements.txt
```

Scraper dependencies are still required (`pip install -r requirements.txt`, Playwright browsers, etc.) — the UI only adds Streamlit.

## Run

```bash
streamlit run ui/app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

## Usage

1. In the sidebar, pick a **scraper** from the dropdown.
2. Click **Run scraper**.
3. Watch the log panel (Rich/print output from `main.py`).
4. Use **Stop** to terminate a long run.
5. After completion, review the **Expected outputs** table (path, exists, line count for JSONL).

## Notes

- Env flags (`PHILRICE`, `IRRI`, `PRISM`, etc.) are set **only for the subprocess** — your `.env` file is not modified.
- One source per run (matches `main.py`).
- Browser-heavy sources (OpenSTAT, PRiSM, IRRI) may open Chromium or need FlareSolverr — same as CLI.

## Files

| File | Role |
|------|------|
| `app.py` | Streamlit layout, run/stop, log panel |
| `runner.py` | Subprocess + background line streaming |
| `sources.py` | Dropdown options, env flags, output paths |
| `utils.py` | ANSI stripping, output file checks |
