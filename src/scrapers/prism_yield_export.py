"""
Buong PRiSM Yield export (CSV) via HTTP — walang browser.

Naglo-loop: bawat Year × Semester × Region (CAR → … → BARMM) × Province,
tapos kinukuha ang municipality table mula sa `yield_province_details`.

Checkpoint: data/checkpoints/prism_yield_export_checkpoint.json
Output: data/prism_processed/prism_yield_export.csv

I-set sa .env: PRISM_JOB=export_yield_csv at PRISM=true, tapos python main.py

**Polite / gov tuning (env):**
  PRISM_EXPORT_DELAY — base sleep pagkatapos ng bawat request (default ~1s)
  PRISM_EXPORT_JITTER — random 0…jitter na idinadagdag (para hindi robotic)
  PRISM_EXPORT_COOLDOWN_EVERY / PRISM_EXPORT_COOLDOWN_SECONDS — extra pahinga tuwing N requests
  PRISM_EXPORT_RETRIES, PRISM_EXPORT_TIMEOUT — POST retry at timeout
"""
from __future__ import annotations

import csv
from datetime import datetime
import json
import os
import random
import re
import time
from typing import Any

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress

from src.config import data_path
from src.utils import require_internet

load_dotenv()
console = Console()

_BASE_SITE = "https://prism.philrice.gov.ph"
BASE = f"{_BASE_SITE}/wp-dynamicreports/map"
_REFERER_PAGE = f"{_BASE_SITE}/wp-dynamicreports"
CSV_PATH = data_path("prism_processed", "prism_yield_export.csv")
CHECKPOINT_PATH = data_path("checkpoints", "prism_yield_export_checkpoint.json")

# CAR una, BARMM huli — numeric regionid gaya ng `loadprovince` / getregionnum
REGION_ORDER: list[tuple[int, str]] = [
    (14, "CAR"),
    (1, "Region I"),
    (2, "Region II"),
    (3, "Region III"),
    (4, "CALABARZON"),
    (17, "MIMAROPA"),
    (5, "Region V"),
    (6, "Region VI"),
    (7, "Region VII"),
    (8, "Region VIII"),
    (9, "Region IX"),
    (10, "Region X"),
    (11, "Region XI"),
    (12, "Region XII"),
    (16, "Region XIII"),
    (15, "BARMM"),
]

SEMESTERS: list[tuple[str, str]] = [
    ("1", "1st Semester (Sept16-Mar15)"),
    ("2", "2nd Semester (Mar16-Sept15)"),
]

# Mas banayad sa gov server: mas mataas ang default kaysa dati
_DELAY = float(os.getenv("PRISM_EXPORT_DELAY", "1.0"))
_JITTER = float(os.getenv("PRISM_EXPORT_JITTER", "0.55"))
_YEAR_MIN = int(os.getenv("PRISM_EXPORT_YEAR_MIN", "2018"))
_YEAR_MAX = int(os.getenv("PRISM_EXPORT_YEAR_MAX", "2026"))
_RETRIES = int(os.getenv("PRISM_EXPORT_RETRIES", "5"))
_TIMEOUT = int(os.getenv("PRISM_EXPORT_TIMEOUT", "90"))
_COOLDOWN_EVERY = int(os.getenv("PRISM_EXPORT_COOLDOWN_EVERY", "75"))
_COOLDOWN_SECONDS = float(os.getenv("PRISM_EXPORT_COOLDOWN_SECONDS", "12"))

CSV_COLUMNS = [
    "Year",
    "Semester",
    "Region",
    "Province",
    "Municipality",
    "Average Yield (ton/ha)",
    "Date and time of Scraping",
]


def _polite_sleep() -> None:
    """Base delay + random jitter — mas natural kaysa fixed interval."""
    extra = random.uniform(0, _JITTER) if _JITTER > 0 else 0.0
    time.sleep(_DELAY + extra)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-PH,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": _BASE_SITE,
            "Referer": _REFERER_PAGE,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    return s


def _post(s: requests.Session, path: str, data: dict[str, Any], timeout: int | None = None) -> str | None:
    url = f"{BASE}/{path.lstrip('/')}"
    to = timeout if timeout is not None else _TIMEOUT
    for attempt in range(_RETRIES):
        try:
            r = s.post(url, data=data, timeout=to)
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", "20"))
                wait = max(5, min(wait, 120))
                console.print(f"[yellow]429 Too Many Requests — naghihintay {wait}s (attempt {attempt + 1}/{_RETRIES})[/yellow]")
                time.sleep(wait)
                continue
            if r.status_code in (502, 503, 504):
                backoff = min(45.0, 3.0 * (2**attempt))
                console.print(
                    f"[yellow]HTTP {r.status_code} — backoff {backoff:.0f}s (attempt {attempt + 1}/{_RETRIES})[/yellow]"
                )
                time.sleep(backoff)
                continue
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            if attempt + 1 >= _RETRIES:
                console.print(f"[red]POST failed {url}: {e}[/red]")
                return None
            time.sleep(min(30.0, 2.0 * (attempt + 1)))
    return None


def parse_provinces(html: str) -> list[tuple[int, str]]:
    if not html:
        return []
    chunk = html.split("<script>", 1)[0]
    out: list[tuple[int, str]] = []
    for m in re.finditer(r'id="prov-(\d+)"[^>]*value="([^"]*)"', chunk):
        out.append((int(m.group(1)), m.group(2).strip()))
    return out


def parse_yield_rows(html: str) -> list[tuple[str, float]]:
    """Municipality + average mula sa yield_province_details HTML."""
    if not html:
        return []
    rows: list[tuple[str, float]] = []
    for m in re.finditer(
        r'<th\s+scope="row"[^>]*>([^<]+)</th>\s*<td[^>]*>\s*([\d.]+)',
        html,
        re.IGNORECASE | re.DOTALL,
    ):
        mun = re.sub(r"\s+", " ", m.group(1)).strip()
        try:
            val = float(m.group(2))
        except ValueError:
            val = 0.0
        rows.append((mun, val))
    return rows


def _ck_key(year: str, sem: str, region_id: int, prov_id: int) -> str:
    return f"{year}|{sem}|{region_id}|{prov_id}"


@require_internet
def run() -> None:
    os.makedirs(os.path.dirname(CSV_PATH) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(CHECKPOINT_PATH) or ".", exist_ok=True)

    done: set[str] = set()
    if os.path.isfile(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, encoding="utf-8") as f:
                data = json.load(f)
            done = set(data.get("done") or [])
        except Exception:
            done = set()

    csv_exists = os.path.isfile(CSV_PATH) and os.path.getsize(CSV_PATH) > 0

    s = _session()
    years = [str(y) for y in range(_YEAR_MIN, _YEAR_MAX + 1)]
    scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Isang loadprovince bawat rehiyon (hindi ulit-ulit per year/sem)
    region_provinces: dict[int, list[tuple[int, str]]] = {}
    for region_id, region_name in REGION_ORDER:
        html = _post(s, "loadprovince", {"regionid": region_id})
        _polite_sleep()
        plist = parse_provinces(html or "")
        region_provinces[region_id] = plist
        if not plist:
            console.print(f"[yellow]Walang province list: region={region_name} (id={region_id})[/yellow]")

    pending: list[tuple[str, str, int, str, int, str]] = []
    for year in years:
        for sem_val, _sem_label in SEMESTERS:
            for region_id, region_name in REGION_ORDER:
                for prov_id, prov_name in region_provinces.get(region_id, []):
                    k = _ck_key(year, sem_val, region_id, prov_id)
                    if k in done:
                        continue
                    pending.append((year, sem_val, region_id, region_name, prov_id, prov_name))

    console.print(f"[dim]Bubuuin ang CSV: {CSV_PATH}[/dim]")
    console.print(f"[dim]Mga bagong kombinasyon (hindi pa sa checkpoint): {len(pending)}[/dim]")
    console.print(
        f"[dim]Polite: delay≈{_DELAY}s + jitter≤{_JITTER}s | cooldown tuwing {_COOLDOWN_EVERY} reqs "
        f"(+{_COOLDOWN_SECONDS}s) | retries={_RETRIES} timeout={_TIMEOUT}s[/dim]"
    )
    if not pending:
        console.print("[green]Wala nang pending combinations sa checkpoint. Walang bagong ie-export.[/green]")
        return

    mode = "a" if csv_exists else "w"
    with open(CSV_PATH, mode, newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS)
        if not csv_exists:
            writer.writeheader()

        with Progress() as progress:
            task = progress.add_task("Yield export", total=max(len(pending), 1))
            detail_requests = 0
            for year, sem_val, region_id, region_name, prov_id, prov_name in pending:
                if (
                    _COOLDOWN_EVERY > 0
                    and detail_requests > 0
                    and detail_requests % _COOLDOWN_EVERY == 0
                ):
                    console.print(
                        f"[dim]Cooldown {_COOLDOWN_SECONDS}s pagkatapos ng {detail_requests} yield requests…[/dim]"
                    )
                    time.sleep(_COOLDOWN_SECONDS)

                detail = _post(
                    s,
                    "yield_province_details",
                    {"year": year, "sem": sem_val, "region": str(region_id), "province": str(prov_id)},
                )
                detail_requests += 1
                _polite_sleep()
                rows = parse_yield_rows(detail or "")

                if not rows:
                    writer.writerow(
                        {
                            "Year": year,
                            "Semester": next(l for v, l in SEMESTERS if v == sem_val),
                            "Region": region_name,
                            "Province": prov_name,
                            "Municipality": "",
                            "Average Yield (ton/ha)": "0",
                            "Date and time of Scraping": scraped_at,
                        }
                    )
                else:
                    sem_label = next(l for v, l in SEMESTERS if v == sem_val)
                    for mun, avg in rows:
                        writer.writerow(
                            {
                                "Year": year,
                                "Semester": sem_label,
                                "Region": region_name,
                                "Province": prov_name,
                                "Municipality": mun,
                                "Average Yield (ton/ha)": str(avg),
                                "Date and time of Scraping": scraped_at,
                            }
                        )

                k = _ck_key(year, sem_val, region_id, prov_id)
                done.add(k)
                with open(CHECKPOINT_PATH, "w", encoding="utf-8") as cf:
                    json.dump({"done": sorted(done)}, cf, indent=2)
                progress.advance(task)

    console.print(f"[green]Tapos. CSV:[/green] {CSV_PATH}")


if __name__ == "__main__":
    run()
