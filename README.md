## Agri-Price Scraper

This project automates the extraction, cleaning, and storage of Philippine agricultural price statistics. It uses Playwright to drive a browser, handles Cloudflare protections, reshapes the exported Excel files into a tidy format, and saves the data both as CSV and into a MySQL database.

### Features

- **Automated scraping** of multiple  URLs defined in `.env` (`URLS`).
- **Antibot handling** via optional FlareSolverr ` and `playwright-stealth`.
- **Robust Excel cleaning** using `pandas`/`numpy`/`scikit-learn` (see `processing.py`).
- **MySQL storage** of cleaned price data via `database.py`.
- **Internet resilience** with automatic connectivity checks and retries (see `utils.py`).

### Project Structure (key files)

- `scraper.py` – main scraper; launches Playwright, paginates years, downloads Excel, calls `download_and_process_excel`, concatenates all data, writes a combined CSV to your Desktop, and stores results in MySQL.
- `processing.py` – functions to read and clean Excel exports (including a manual “drop-in Excel files and process them” workflow via `process_manual_downloads`).
- `utils.py` – helpers for network/selector retry logic and connectivity checks.
- `database.py` – `store_data_in_mysql` which recreates and populates the `price_data` table.
- `.env` – configuration for database connection, OpenSTAT URLs, and cleaning rules.

### Requirements

- **Python** 3.9+ recommended.
- **MySQL** server with a database created (see `MYSQL_DATABASE` in `.env`).
- A modern Chromium-based browser (Chrome/Edge/Chromium) for Playwright.

Python dependencies are listed in `requirements.txt` and include:

- `playwright`, `playwright-stealth`
- `pandas`, `numpy`, `scikit-learn`, `openpyxl`
- `mysql-connector-python` and/or `mysqlclient`
- `python-dotenv`, `requests`, `rich`, `flask`, etc.

### Setup

1. **Create and activate a virtual environment (optional but recommended).**
2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**

   ```bash
   python -m playwright install
   ```

4. **Configure `.env`:**

   - `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` – MySQL connection.
   - `URLS` – comma-separated list of OpenSTAT URLs to scrape.
   - `UNWANTED_TEXTS` – phrases/footnotes to drop from the cleaned data.
   - `RESUME_CHECKPOINT` – set to `true` to resume from a checkpointed URL index, or `false` to start from scratch.

5. **Prepare MySQL:**

   - Ensure a database exists matching `MYSQL_DATABASE` in `.env`.
   - `store_data_in_mysql` will drop and recreate a `price_data` table on each run.

### Running the scraper

From the project root:

```bash
python scraper.py
```

This will:

- Launch a browser and navigate through each URL in `URLS`.
- Select all required dropdown values and iterate over available years in safe batches.
- Download and clean Excel exports using `processing.py`.
- Save a combined CSV to a folder like `~/Desktop/Agri-Price-Data_Files/`.
- Insert all rows into the `price_data` MySQL table.

If Cloudflare or the site blocks automated access, you can still:

- Log into OpenSTAT with a normal browser,
- Download the Excel files manually into the `manual_downloads` folder in the project root,
- Use the helpers in `processing.py` (e.g., `process_manual_downloads`) from a Python session to produce a cleaned DataFrame that you can then export or store.

### Notes

- Do **not** commit your `.env` to version control; it contains credentials and environment-specific settings.
- This README intentionally focuses on the scraping and processing pipeline and does not document any separate research or notes markdown files in the repo.
