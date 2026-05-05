"""
Prism scraper — PRiSM Data Products at iba pang sources.

**PRiSM (philrice) Data Products:** Ang pahinang `/dataproducts/` ay WordPress wrapper lang;
ang interactive dashboard ay naka-embed sa:
  https://prism.philrice.gov.ph/wp-dynamicreports
Kaya default ay i-rewrite ang `/dataproducts/` → `wp-dynamicreports` (tingnan PRISM_REWRITE_DATAPRODUCTS_TO_APP).

Ang app ay JS-heavy (jQuery, Leaflet, DataTables, AJAX sa `/wp-dynamicreports/map/...`).
Itong Prism browser scrape ay **Scrapling lang** (walang Playwright branch dito).
Default: **stealth** (StealthySession) + opsyonal na Cloudflare bypass — mas angkop sa gov / posibleng anti-bot.
Kung kailangan mas mabilis at walang CF: PRISM_SCRAPLING_MODE=dynamic. Patuloy na PRISM_JS_SETTLE_SECONDS (hal. 8+).

Para sa buong Yield CSV (lahat rehiyon/taon), gumamit ng PRISM_JOB=export_yield_csv (HTTP).

Setup (Scrapling): pip install -r requirements-prism.txt && scrapling install
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
from typing import Any

from dotenv import load_dotenv
from rich.console import Console

from src.agri_corpus.scraper_utils import load_checkpoint, save_checkpoint
from src.agri_corpus.text_utils import safe_id_from_url
from src.config import data_path
from src.utils import require_internet


load_dotenv()
console = Console()

try:
    from scrapling.fetchers import (
        DynamicSession,
        FetcherSession,
        StealthyFetcher,
        StealthySession,
    )

    HAS_SCRAPLING = True
except ImportError:
    HAS_SCRAPLING = False
    DynamicSession = FetcherSession = StealthyFetcher = StealthySession = None  # type: ignore[misc, assignment]

PRISM_URLS_ENV = (os.getenv("PRISM_URLS") or os.getenv("PRISM_URL") or "").strip()
PRISM_JSONL = data_path("prism_processed", "prism_corpus.jsonl")
PRISM_TXT_DIR = data_path("prism_txt")
PRISM_PDFS_DIR = data_path("prism_pdfs")
CHECKPOINT_PATH = data_path("checkpoints", "prism_checkpoint.json")

SCRAPLING_MODE = (os.getenv("PRISM_SCRAPLING_MODE") or "stealth").strip().lower()
_HEADLESS = os.getenv("PRISM_HEADLESS", os.getenv("HEADLESS", "true")).strip().lower() != "false"
_DELAY_PAGE = float(os.getenv("PRISM_DELAY_PAGE", "2"))
_MIN_LEN = int(os.getenv("PRISM_MIN_CONTENT_LEN", "100"))
_RESUME = (os.getenv("PRISM_RESUME_CHECKPOINT", "true").strip().lower() in ("true", "1", "yes"))

_IMPERSONATE = (os.getenv("PRISM_IMPERSONATE") or "chrome").strip()
_USE_HTTP3 = os.getenv("PRISM_HTTP3", "false").strip().lower() in ("true", "1", "yes")
# Gov / CDN: default naka-on ang CF/Turnstile hooks (i-set false kung mabagal o hindi kailangan)
_SOLVE_CF = os.getenv("PRISM_SOLVE_CLOUDFLARE", "true").strip().lower() in ("true", "1", "yes")
_CONTENT_SELECTOR = (os.getenv("PRISM_CONTENT_SELECTOR") or "").strip()
_ADAPTIVE = os.getenv("PRISM_ADAPTIVE", "false").strip().lower() in ("true", "1", "yes")
_AUTO_SAVE = os.getenv("PRISM_AUTO_SAVE", "false").strip().lower() in ("true", "1", "yes")
_STEALTH_CLASS_ADAPTIVE = os.getenv("PRISM_STEALTH_FETCHER_ADAPTIVE", "true").strip().lower() in (
    "true",
    "1",
    "yes",
)

_REWRITE_DATAPRODUCTS = os.getenv("PRISM_REWRITE_DATAPRODUCTS_TO_APP", "true").strip().lower() in (
    "true",
    "1",
    "yes",
)
_JS_SETTLE = float(os.getenv("PRISM_JS_SETTLE_SECONDS", "8"))


def _parse_seed_urls(raw: str) -> list[str]:
    parts = re.split(r"[\s,]+", raw)
    return [p.strip() for p in parts if p.strip() and p.startswith(("http://", "https://"))]


def _normalize_prism_target_url(url: str) -> str:
    """Ang /dataproducts/ ay iframe lang — direktahin ang wp-dynamicreports kung naka-on ang rewrite."""
    if not _REWRITE_DATAPRODUCTS:
        return url
    try:
        p = urllib.parse.urlparse(url)
    except Exception:
        return url
    host = (p.netloc or "").lower()
    path = (p.path or "").lower().rstrip("/")
    if "prism.philrice.gov.ph" not in host:
        return url
    if path.endswith("/dataproducts") or "/dataproducts/" in path or path == "/dataproducts":
        return urllib.parse.urlunparse(
            (
                p.scheme or "https",
                "prism.philrice.gov.ph",
                "/wp-dynamicreports",
                "",
                "",
                "",
            )
        )
    return url


def _is_prism_dynamic_app(url: str) -> bool:
    return "prism.philrice.gov.ph" in url.lower() and "wp-dynamicreports" in url.lower()


def _append_jsonl(record: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _safe_txt_name(url: str) -> str:
    safe = re.sub(r"[^\w\-.]", "_", url) or "prism_page"
    base = safe[:180] if len(safe) > 180 else safe
    return base if base.lower().endswith(".txt") else f"{base}.txt"


def _page_plain_text(page: Any) -> str:
    try:
        chunks = page.xpath(
            "//body//text()[not(ancestor::script) and not(ancestor::style)]"
        ).getall()
    except Exception:
        chunks = page.css("body *::text").getall()
    return "\n".join(c.strip() for c in chunks if c and str(c).strip())


def _page_title(page: Any) -> str:
    t = page.css("title::text").get()
    if t and t.strip():
        return t.strip()
    h1 = page.css("h1::text").get()
    return (h1 or "").strip()


def _css_with_adaptive(page: Any, selector: str) -> Any:
    kw: dict[str, Any] = {}
    if _ADAPTIVE:
        kw["adaptive"] = True
    if _AUTO_SAVE:
        kw["auto_save"] = True
    return page.css(selector, **kw) if kw else page.css(selector)


def _text_from_selector(page: Any, selector: str) -> str:
    blocks = _css_with_adaptive(page, selector)
    lines: list[str] = []
    try:
        for el in blocks:
            try:
                for chunk in el.xpath(".//text()[not(ancestor::script) and not(ancestor::style)]").getall():
                    s = (chunk or "").strip()
                    if s:
                        lines.append(s)
            except Exception:
                continue
    except TypeError:
        try:
            lines = [
                c.strip()
                for c in blocks.xpath(".//text()[not(ancestor::script) and not(ancestor::style)]").getall()
                if (c or "").strip()
            ]
        except Exception:
            lines = []
    return "\n".join(lines)


def _content_selectors_for_url(norm_url: str) -> list[str]:
    if _CONTENT_SELECTOR:
        return [s.strip() for s in _CONTENT_SELECTOR.split(",") if s.strip()]
    if _is_prism_dynamic_app(norm_url):
        # detail_info = "Detailed report" table/charts; content-body = buong panel
        return ["#detail_info", "#content-body"]
    return []


def _extract_body_text_scrapling(page: Any, norm_url: str) -> str:
    for sel in _content_selectors_for_url(norm_url):
        focused = _text_from_selector(page, sel).strip()
        if len(focused) >= _MIN_LEN:
            return focused
    return _page_plain_text(page)


def _maybe_js_settle(norm_url: str) -> None:
    if _is_prism_dynamic_app(norm_url) and _JS_SETTLE > 0:
        console.print(f"[dim]JS settle { _JS_SETTLE }s (PRiSM app)…[/dim]")
        time.sleep(_JS_SETTLE)


def _persist_record(
    raw_url: str,
    norm_url: str,
    title: str,
    text: str,
    scraped: set[str],
    checkpoint: dict,
) -> None:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < _MIN_LEN:
        console.print(f"[yellow]Masyadong maikli ang text ({len(text)} chars); hindi isinulat sa JSONL.[/yellow]")
        return

    doc_id = safe_id_from_url(norm_url)
    record: dict[str, Any] = {
        "text": text,
        "input": text,
        "content": text,
        "source": "prism",
        "url": norm_url,
        "title": title,
        "doc_id": doc_id,
    }
    if raw_url != norm_url:
        record["original_url"] = raw_url

    _append_jsonl(record, PRISM_JSONL)
    txt_path = os.path.join(PRISM_TXT_DIR, _safe_txt_name(norm_url))
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError:
        pass
    scraped.add(norm_url)
    checkpoint["scraped_urls"] = sorted(scraped)
    save_checkpoint(CHECKPOINT_PATH, checkpoint)
    console.print(f"[green]OK[/green] — {len(text)} chars, title={title[:60]!r}{'…' if len(title) > 60 else ''}")


def _process_scrapling_page(raw_url: str, norm_url: str, page: Any, scraped: set[str], checkpoint: dict) -> None:
    try:
        title = _page_title(page)
        text = _extract_body_text_scrapling(page, norm_url)
    except Exception as e:
        console.print(f"[red]Parse error: {e}[/red]")
        return
    _persist_record(raw_url, norm_url, title, text, scraped, checkpoint)


def _urls_to_process(urls: list[str], scraped: set[str]) -> list[tuple[str, str]]:
    """List of (raw_url, normalized_url)."""
    out: list[tuple[str, str]] = []
    for raw in urls:
        norm = _normalize_prism_target_url(raw)
        if _RESUME and norm in scraped:
            short = norm[:80] + "…" if len(norm) > 80 else norm
            console.print(f"[dim]Skip (checkpoint): {short}[/dim]")
            continue
        if raw != norm:
            console.print(f"[dim]Target: {norm}[/dim] (mula sa dataproducts wrapper)")
        out.append((raw, norm))
    return out


def _run_fetch_session(pending: list[tuple[str, str]], scraped: set[str], checkpoint: dict) -> None:
    assert FetcherSession is not None
    session_kw: dict[str, Any] = {"impersonate": _IMPERSONATE}
    if _USE_HTTP3:
        session_kw["http3"] = True
    with FetcherSession(**session_kw) as session:
        for raw, norm in pending:
            console.print(f"[bold]→[/bold] {norm}")
            try:
                page = session.get(norm, stealthy_headers=True)
            except Exception as e:
                console.print(f"[red]Fetch error: {e}[/red]")
                time.sleep(_DELAY_PAGE)
                continue
            _maybe_js_settle(norm)
            _process_scrapling_page(raw, norm, page, scraped, checkpoint)
            time.sleep(_DELAY_PAGE)


def _run_stealth_session(pending: list[tuple[str, str]], scraped: set[str], checkpoint: dict) -> None:
    assert StealthySession is not None and StealthyFetcher is not None
    if _STEALTH_CLASS_ADAPTIVE:
        StealthyFetcher.adaptive = True
        console.print("[dim]StealthyFetcher.adaptive = True (class)[/dim]")
    session_kw: dict[str, Any] = {"headless": _HEADLESS}
    if _SOLVE_CF:
        session_kw["solve_cloudflare"] = True
        console.print("[dim]StealthySession: solve_cloudflare=True[/dim]")
    with StealthySession(**session_kw) as session:
        for raw, norm in pending:
            console.print(f"[bold]→[/bold] {norm}")
            try:
                try:
                    page = session.fetch(norm, google_search=False)
                except TypeError:
                    page = session.fetch(norm)
            except Exception as e:
                console.print(f"[red]Fetch error: {e}[/red]")
                time.sleep(_DELAY_PAGE)
                continue
            _maybe_js_settle(norm)
            _process_scrapling_page(raw, norm, page, scraped, checkpoint)
            time.sleep(_DELAY_PAGE)


def _run_dynamic_session(pending: list[tuple[str, str]], scraped: set[str], checkpoint: dict) -> None:
    assert DynamicSession is not None
    session_kw: dict[str, Any] = {
        "headless": _HEADLESS,
        "disable_resources": False,
        "network_idle": True,
    }
    with DynamicSession(**session_kw) as session:
        for raw, norm in pending:
            console.print(f"[bold]→[/bold] {norm}")
            try:
                try:
                    page = session.fetch(norm, network_idle=True)
                except TypeError:
                    page = session.fetch(norm)
            except Exception as e:
                console.print(f"[red]Fetch error: {e}[/red]")
                time.sleep(_DELAY_PAGE)
                continue
            _maybe_js_settle(norm)
            _process_scrapling_page(raw, norm, page, scraped, checkpoint)
            time.sleep(_DELAY_PAGE)


@require_internet
def run():
    prism_job = (os.getenv("PRISM_JOB") or "").strip().lower()
    if prism_job in ("export_yield_csv", "export_yield"):
        console.rule("[bold cyan]Prism – Buong Yield CSV (HTTP API)[/bold cyan]")
        from src.scrapers.prism_yield_export import run as run_yield_export

        run_yield_export()
        return

    console.rule("[bold cyan]Prism – Scrape[/bold cyan]")
    console.print(f"[dim]JSONL: {PRISM_JSONL}[/dim]")
    console.print(
        f"[dim]Scrapling mode={SCRAPLING_MODE} | solve_cloudflare={_SOLVE_CF} | "
        f"rewrite_dataproducts={_REWRITE_DATAPRODUCTS} | js_settle={_JS_SETTLE}s[/dim]"
    )
    if _CONTENT_SELECTOR:
        console.print(f"[dim]PRISM_CONTENT_SELECTOR={_CONTENT_SELECTOR!r}[/dim]")

    urls = _parse_seed_urls(PRISM_URLS_ENV)
    if not urls:
        console.print(
            "[yellow]Walang valid na PRISM_URL / PRISM_URLS. Halimbawa para sa PRiSM Data Products:\n"
            "  PRISM_URL=https://prism.philrice.gov.ph/dataproducts/[/yellow]"
        )
        return

    os.makedirs(PRISM_TXT_DIR, exist_ok=True)
    os.makedirs(PRISM_PDFS_DIR, exist_ok=True)

    checkpoint: dict = load_checkpoint(CHECKPOINT_PATH, default={"scraped_urls": []})
    scraped: set[str] = set(checkpoint.get("scraped_urls") or [])
    pending = _urls_to_process(urls, scraped)
    if not pending:
        console.print("[dim]Walang bagong URL na kailangan i-scrape.[/dim]")
        return

    if not HAS_SCRAPLING:
        console.print(
            "[red]Scrapling hindi naka-install.[/red] "
            "[dim]pip install -r requirements-prism.txt[/dim] tapos [dim]scrapling install[/dim]"
        )
        return

    if SCRAPLING_MODE not in ("fetch", "stealth", "dynamic"):
        console.print(
            f"[red]Hindi valid ang PRISM_SCRAPLING_MODE={SCRAPLING_MODE!r}; "
            "gamitin: fetch, stealth, dynamic.[/red]"
        )
        return

    console.print(
        f"[dim]Scrapling: mode={SCRAPLING_MODE} | impersonate={_IMPERSONATE} | http3={_USE_HTTP3} | "
        f"headless={_HEADLESS}[/dim]"
    )

    if SCRAPLING_MODE == "fetch":
        console.print(
            "[yellow]Babala: fetch mode ay mahina para sa PRiSM wp-dynamicreports (JS app). "
            "Subukan PRISM_SCRAPLING_MODE=stealth (default) o dynamic.[/yellow]"
        )
        _run_fetch_session(pending, scraped, checkpoint)
    elif SCRAPLING_MODE == "stealth":
        _run_stealth_session(pending, scraped, checkpoint)
    else:
        _run_dynamic_session(pending, scraped, checkpoint)


if __name__ == "__main__":
    run()
