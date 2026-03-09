from playwright.sync_api import sync_playwright
from utils import require_internet, wait_for_selector_with_retry, wait_for_internet
from processing import download_and_process_excel
from database import store_data_in_mysql
from dotenv import load_dotenv
from rich.console import Console
from datetime import datetime
import os
import json
import pandas as pd
import time

try:
    from bypass import get_cloudflare_cookies
except ImportError:
    get_cloudflare_cookies = lambda: []

try:
    from playwright_stealth import stealth_sync
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

# Initialize
console = Console()
load_dotenv()
urls = os.getenv("URLS").split(",")

timestamp = datetime.now().strftime("%B%d,%Y_%H-%M-%S")

@require_internet
def select_dropdown_options(page, year_indexes, finalize=False):
    """Select all fixed dropdowns and optionally the year + Excel option"""
    selectors = [
        "#ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_VariableSelectorValueSelectRepeater_ctl01_VariableValueSelect_VariableValueSelect_ValuesListBox",
        "#ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_VariableSelectorValueSelectRepeater_ctl02_VariableValueSelect_VariableValueSelect_ValuesListBox",
        "#ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_VariableSelectorValueSelectRepeater_ctl04_VariableValueSelect_VariableValueSelect_ValuesListBox",
    ]
    year_selector = "#ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_VariableSelectorValueSelectRepeater_ctl03_VariableValueSelect_VariableValueSelect_ValuesListBox"

    for selector in selectors:
        wait_for_selector_with_retry(page, selector)
        page.eval_on_selector(selector, """
            el => {
                Array.from(el.options).forEach(opt => opt.selected = true);
                el.dispatchEvent(new Event('change'));
            }
        """)
        page.wait_for_timeout(1500)

    # Handle year selection
    wait_for_selector_with_retry(page, year_selector)
    page.eval_on_selector(year_selector, """
        el => {
            Array.from(el.options).forEach(opt => opt.selected = false);
            el.dispatchEvent(new Event('change'));
        }
    """)
    for idx in year_indexes:
        page.eval_on_selector(year_selector, f"""
            el => {{
                el.options[{idx}].selected = true;
                el.dispatchEvent(new Event('change'));
            }}
        """)
        page.wait_for_timeout(500)

    if finalize:
        format_selector = "select#ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_OutputFormats_OutputFormats_OutputFormatDropDownList"
        for attempt in range(3):
            try:
                page.select_option(format_selector, value="FileTypeExcelX", timeout=30000)
                break
            except Exception:
                if attempt == 2:
                    raise
                console.print(f"[yellow]Retrying Excel format selection (Attempt {attempt+2}/3)...[/yellow]")
                page.wait_for_timeout(3000)


def ensure_beginning_of_row_checked(page, variable_title: str):
    """
    Ticks 'Beginning of row' checkbox inside the variable panel (e.g., Commodity, Geolocation, Period).
    Ginagamit natin para siguradong nasa rows ang mga dimension para maging proper columns sa Excel.
    """
    # Hanapin ang panel base sa title text (Commodity / Geolocation / Period / Year)
    panel = page.locator(
        f"xpath=//div[.//text()[contains(normalize-space(.), '{variable_title}')]]"
    ).first

    # Checkbox na may label na 'Beginning of row' sa loob ng panel
    cb = panel.locator(
        "xpath=.//input[@type='checkbox' and (following-sibling::label[contains(., 'Beginning of row')] "
        "or parent::label[contains(., 'Beginning of row')] "
        "or @id=//label[contains(., 'Beginning of row')]/@for)]"
    ).first

    # Fallback: global search kung hindi mahanap sa panel
    if cb.count() == 0:
        label = page.locator("xpath=//label[contains(., 'Beginning of row')]").first
        if label.count() == 0:
            return
        label.click()
        page.wait_for_timeout(300)
        return

    # I-tick kung hindi pa naka-check
    if not cb.is_checked():
        cb.check()
        page.wait_for_timeout(300)


# Folder kung saan ilalagay ang na-download na Excel (temporary) mula sa OpenSTAT
SCRAPER_DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraper_downloads")

# Sa website ng OpenStat: "Number of selected cells exceeds the maximum allowed 100,000".
# Nagdadagdag tayo ng years isa-isa; kapag lumabas ang error sa site, hihinto at gagamitin ang last good selection (bawas taon).
# Safety cap: max years per selection para hindi masyadong mabigat sa isang request (optional).
MAX_YEARS_PER_SELECTION_SAFETY = 50

# Checkpoint file for resume: when RESUME_CHECKPOINT=true we skip URLs in completed_url_indices
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_PATH = os.path.join(_PROJECT_DIR, "scraper_checkpoint.json")


def _load_checkpoint():
    """Load checkpoint if exists. Returns set of completed url indices."""
    if not os.path.isfile(CHECKPOINT_PATH):
        return set()
    try:
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("completed_url_indices", []))
    except Exception:
        return set()


def _save_checkpoint(completed_url_indices):
    """Save checkpoint with completed URL indices."""
    try:
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
            json.dump({"completed_url_indices": sorted(completed_url_indices)}, f, indent=2)
    except Exception as e:
        console.print(f"[dim]Could not save checkpoint: {e}[/dim]")


def _page_is_cloudflare_522(page):
    """True if current page is Cloudflare Error 522 (connection timed out to origin)."""
    try:
        content = page.content()
        return "Error code 522" in content or ("Connection timed out" in content and "Cloudflare" in content)
    except Exception:
        return False


@require_internet
def scrape_all():
    all_data_frames = []
    console.rule(f"[bold cyan]Agri-Price Scraper Started at {timestamp}")

    os.makedirs(SCRAPER_DOWNLOADS_DIR, exist_ok=True)
    downloads_path = os.path.abspath(SCRAPER_DOWNLOADS_DIR)

    # Anti-detection args; i-set ang download folder para hindi magulo ang Windows Downloads
    launch_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-automation",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        f'--download-default-directory="{downloads_path}"',
    ]

    with sync_playwright() as p:
        # Chrome muna para tumugma sa FlareSolverr (Chrome ang gamit nito sa Docker)
        try:
            browser = p.chromium.launch(
                headless=False,
                channel="chrome",
                args=launch_args,
            )
            console.print(f"[dim]Using Google Chrome (stealth). Excel downloads → {downloads_path}[/dim]")
        except Exception:
            try:
                browser = p.chromium.launch(
                    headless=False,
                    channel="msedge",
                    args=launch_args,
                )
                console.print(f"[dim]Using Microsoft Edge (stealth). Excel downloads → {downloads_path}[/dim]")
            except Exception:
                browser = p.chromium.launch(headless=False, args=launch_args)
                console.print(f"[dim]Using Chromium (stealth). Excel downloads → {downloads_path}[/dim]")

        # Kunin muna bypass cookies (at User-Agent mula FlareSolverr) bago gumawa ng context
        first_url = next((u.strip() for u in urls if u and u.strip()), None)
        bypass_cookies, bypass_user_agent = get_cloudflare_cookies(first_url, log=lambda msg: console.print(msg))

        context_options = {
            "viewport": {"width": 1280, "height": 720},
            "locale": "en-PH",
            "ignore_https_errors": False,
            "java_script_enabled": True,
            "bypass_csp": False,
        }
        if bypass_user_agent:
            context_options["user_agent"] = bypass_user_agent
            console.print("[dim]Gamit ang User-Agent mula FlareSolverr (para tumugma ang session).[/dim]")
        context = browser.new_context(**context_options)

        if bypass_cookies:
            try:
                context.add_cookies(bypass_cookies)
                console.print("[green]Cloudflare bypass: cookies injected.[/green]")
            except Exception as e:
                console.print(f"[dim]Bypass cookies skip: {e}[/dim]")
        else:
            console.print("[dim]Walang nakuha na bypass cookies. Maghintay sa Cloudflare o gamitin manual mode.[/dim]")

        page = context.new_page()

        if HAS_STEALTH:
            try:
                stealth_sync(page)
                console.print("[dim]Stealth evasions applied.[/dim]")
            except Exception as e:
                console.print(f"[dim]Stealth skip: {e}[/dim]")
        else:
            console.print("[dim]Install playwright-stealth for better bypass: pip install playwright-stealth[/dim]")

        page.set_default_timeout(60000)
        # Maikling delay bago unang navigation (parang human)
        time.sleep(1)

        # Checkpoint: resume = skip already-completed URLs; false = start from scratch
        resume_checkpoint = os.getenv("RESUME_CHECKPOINT", "false").strip().lower() in ("true", "1", "yes")
        if resume_checkpoint:
            completed_url_indices = _load_checkpoint()
            if completed_url_indices:
                console.print(f"[dim]Resume mode: will skip URL indices already in checkpoint: {sorted(completed_url_indices)}[/dim]")
        else:
            completed_url_indices = set()
            if os.path.isfile(CHECKPOINT_PATH):
                try:
                    os.remove(CHECKPOINT_PATH)
                    console.print("[dim]Checkpoint cleared (RESUME_CHECKPOINT=false). Starting from first URL.[/dim]")
                except Exception:
                    pass

        for url_index, url in enumerate(urls):
            if url_index in completed_url_indices:
                console.print(f"[dim]Skipping URL {url_index + 1}/{len(urls)} (already completed in checkpoint).[/dim]")
                continue
            console.rule(f"[bold green]Processing URL {url_index + 1}/{len(urls)}")
            # Navigate: on timeout/522 we skip this link and continue with next
            if not navigate_with_retries(page, url):
                console.print(f"[yellow]Skipping URL {url_index + 1} (connection timeout or Error 522). Continuing next URL...[/yellow]")
                continue
            try:
                wait_for_cloudflare_check(page, url_index)
            except Exception as e:
                console.print(f"[yellow]Skipping URL {url_index + 1} (Cloudflare check failed: {e}). Continuing next URL...[/yellow]")
                continue

            # Siguraduhing naka-'Beginning of row' ang pangunahing dimensions
            try:
                ensure_beginning_of_row_checked(page, "Geolocation")
                ensure_beginning_of_row_checked(page, "Commodity")
                ensure_beginning_of_row_checked(page, "Period")
            except Exception as e:
                console.print(f"[dim]Skipping 'Beginning of row' tweak (non-fatal): {e}[/dim]")

            year_selector = "#ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_VariableSelectorValueSelectRepeater_ctl03_VariableValueSelect_VariableValueSelect_ValuesListBox"
            wait_for_selector_with_retry(page, year_selector, timeout=30000)
            total_years = page.eval_on_selector(year_selector, "el => el.options.length")
            console.print(f"[bold blue]Years available:[/bold blue] {total_years}")
            console.print(f"[dim]Per batch: magdadagdag ng years hanggang 100k limit ng site; ang natitirang years kukunin sa susunod na batch hanggang maubos lahat.[/dim]")

            remaining_years = list(range(total_years))
            url_skipped_due_to_error = False  # True if we skip rest of URL due to 522/timeout
            url_data_frames = []  # Per-URL list so we can apply row cap before adding to all_data_frames

            while remaining_years:
                console.print(f"[dim]--- Batch: kukunin ang {len(remaining_years)} natitirang taon ---[/dim]")
                current_batch = []
                for year_idx in remaining_years:
                    # Safety: huwag lumampas ng 50 years sa isang selection
                    if len(current_batch) >= MAX_YEARS_PER_SELECTION_SAFETY:
                        console.print(f"[dim]Safety cap ({MAX_YEARS_PER_SELECTION_SAFETY} years) reached.[/dim]")
                        break
                    test_batch = current_batch + [year_idx]
                    console.print(f"[dim]Testing selection:[/dim] {len(test_batch)} years (adding year index {year_idx})")

                    if not navigate_with_retries(page, url):
                        console.print(f"[yellow]Connection failed (522/timeout). Skipping rest of URL {url_index + 1}.[/yellow]")
                        remaining_years = []
                        url_skipped_due_to_error = True
                        break
                    try:
                        wait_for_cloudflare_check(page, url_index)
                    except Exception:
                        remaining_years = []
                        url_skipped_due_to_error = True
                        break
                    select_dropdown_options(page, test_batch)

                    try:
                        # Galing sa website: "Number of selected cells exceeds the maximum allowed 100,000"
                        is_error = page.is_visible(
                            "#ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_SelectionErrorlabel",
                            timeout=5000
                        )
                        if is_error:
                            console.print("[yellow]Lumabas sa site: lumampas sa 100,000 cells. Gagamitin ang nakaraang selection; ang natitirang years sa susunod na batch.[/yellow]")
                            break
                        else:
                            current_batch = test_batch
                    except Exception as e:
                        console.print(f"[red]Error checking selection: {e}[/red]")
                        break

                if not current_batch:
                    if not remaining_years:
                        break
                    skipped = remaining_years.pop(0)
                    console.print(f"[red]Skipped year index:[/red] {skipped}")
                    continue

                # Finalize dropdowns and download
                if not navigate_with_retries(page, url):
                    console.print(f"[yellow]Connection failed (522/timeout). Skipping rest of URL {url_index + 1}.[/yellow]")
                    remaining_years = []
                    url_skipped_due_to_error = True
                else:
                    try:
                        wait_for_cloudflare_check(page, url_index)
                    except Exception:
                        remaining_years = []
                        url_skipped_due_to_error = True
                if not remaining_years:
                    break
                select_dropdown_options(page, current_batch, finalize=True)
                # Kunin ang selected commodity label(s) sa page para gamitin kung ang Excel ay "Cereals" lang ang lalabas
                commodity_selector = "#ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_VariableSelectorValueSelectRepeater_ctl02_VariableValueSelect_VariableValueSelect_ValuesListBox"
                selected_commodity_labels = []
                try:
                    selected_commodity_labels = page.eval_on_selector(
                        commodity_selector,
                        "el => Array.from(el.options).filter(o => o.selected).map(o => o.text.trim())"
                    ) or []
                except Exception:
                    pass

                try:
                    submit_button = page.wait_for_selector("input[type='submit']", timeout=120000)
                    submit_button.click()
                    # "load" lang para hindi ma-stuck sa networkidle (mabigat ang OpenSTAT)
                    page.wait_for_load_state("load", timeout=90000)

                    cleaned_data = download_and_process_excel(
                        page, url_index, timestamp, urls,
                        selected_commodity_labels=selected_commodity_labels
                    )
                    if not cleaned_data.empty:
                        url_data_frames.append(cleaned_data)
                        batch_rows = len(cleaned_data)
                        total_this_url = sum(len(df) for df in url_data_frames)
                        console.print(f"[green]✔ Processed selection:[/green] {len(current_batch)} years [dim](batch: {batch_rows} rows, total this URL: {total_this_url})[/dim]")
                    else:
                        console.print("[yellow]No data returned[/yellow]")

                except Exception as e:
                    console.print(f"[red] Submission error:[/red] {e}")

                remaining_years = [y for y in remaining_years if y not in current_batch]
                if remaining_years:
                    console.print(f"[dim]Natitirang taon sa URL na ito: {len(remaining_years)} — kukunin sa susunod na batch.[/dim]")
                else:
                    console.print(f"[dim]Lahat ng taon sa URL na ito nakuha na.[/dim]")

            all_data_frames.extend(url_data_frames)

            # Save checkpoint only when we finished this URL without skipping due to 522/timeout
            if not url_skipped_due_to_error:
                completed_url_indices.add(url_index)
                _save_checkpoint(completed_url_indices)
                console.print(f"[dim]Checkpoint saved: URL {url_index + 1} marked complete.[/dim]")

        browser.close()

    if all_data_frames:
        final_df = pd.concat(all_data_frames, ignore_index=True)
        # Siguraduhing may Commodity column para makita ng supervisor (Rice, Cereals, etc.)
        if "Commodity" not in final_df.columns:
            final_df["Commodity"] = final_df.get("Commodity Type", "N/A")
        # Ayos ng column order: Geolocation, Commodity Type, Commodity, Year, Month, Price
        col_order = ["Geolocation", "Commodity Type", "Commodity", "Year", "Month", "Price"]
        final_df = final_df[[c for c in col_order if c in final_df.columns]]
        output_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Agri-Price-Data_Files")
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f"openstat_with_commodity_{timestamp}.csv")
        final_df.to_csv(output_file, index=False)
        console.print(f"[bold green]✔ Saved combined file (may Commodity column):[/bold green] {output_file}")

        store_data_in_mysql(final_df)
        # Ipaalam kung saan makikita ang CSV pag successful
        output_dir_abs = os.path.abspath(output_dir)
        console.print(f"[bold cyan]Lahat ng CSV ay nandito:[/bold cyan] [green]{output_dir_abs}[/green]")
    else:
        console.print("[bold red]No data was scraped![/bold red]")

    console.rule("[bold cyan]Scraper Finished")


def wait_for_cloudflare_check(page, url_index, timeout=300000):
    """Hintayin ang Cloudflare: auto-verification (5–25s) o manual 'Verify you are human'."""
    year_selector = "#ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_VariableSelectorValueSelectRepeater_ctl03_VariableValueSelect_VariableValueSelect_ValuesListBox"
    try:
        page.wait_for_selector(year_selector, timeout=8000)
        return
    except Exception:
        pass
    # "Performing security verification" – minsan naa-auto complete sa 10–20s
    console.print("[dim]Nakita ang Cloudflare. Naghihintay hanggang 20s kung aano-verify...[/dim]")
    for _ in range(4):
        time.sleep(5)
        try:
            if page.query_selector(year_selector):
                console.print("[green]Nakapasok na (auto). Tuloy ang scrape.[/green]")
                return
        except Exception:
            pass
    # Kung may checkbox / CAPTCHA, kailangan i-click ng user
    console.print("[yellow]Kung nakikita mo ang 'Verify you are human', i-click mo ang checkbox sa browser.[/yellow]")
    console.print("[yellow]Kung may CAPTCHA, sagutin mo. Naghihintay hanggang 5 minuto...[/yellow]")
    try:
        page.wait_for_selector(year_selector, timeout=timeout)
        console.print("[green]Nakapasok na. Tuloy ang scrape.[/green]")
    except Exception as e:
        console.print(f"[red]Timeout: hindi lumabas ang OpenSTAT. {e}[/red]")
        console.print("[yellow]Gamitin ang manual mode: mag-download sa normal browser, ilagay sa manual_downloads, then: python run_manual.py[/yellow]")
        raise


MAX_NAV_ATTEMPTS = 4  # Huwag mag-retry nang walang hanggan sa timeout


def navigate_with_retries(page, url, timeout=45000):
    """
    Navigate to a URL, retrying on errors. Max MAX_NAV_ATTEMPTS tries.
    Returns True on success, False if we give up (caller should skip this URL).
    Raises on fatal errors (e.g. browser closed).
    """
    attempt = 1
    while attempt <= MAX_NAV_ATTEMPTS:
        try:
            print(f"→ Navigating to URL (Attempt {attempt}/{MAX_NAV_ATTEMPTS})...")
            page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            page.wait_for_load_state("load", timeout=30000)
            # Error 522 = connection timed out between Cloudflare and origin (openstat.psa.gov.ph)
            if _page_is_cloudflare_522(page):
                console.print(f"[yellow]Cloudflare Error 522 (origin server did not respond). Retry {attempt}/{MAX_NAV_ATTEMPTS}.[/yellow]")
                attempt += 1
                time.sleep(5)
                continue
            return True
        except Exception as e:
            err_str = str(e)
            print(f"Navigation error: {e}")

            if "Target" in err_str and "closed" in err_str:
                console.print("[red]Browser o page na-close. Huwag isara ang window habang tumatakbo ang scraper.[/red]")
                raise

            if "ERR_NAME_NOT_RESOLVED" in err_str or "ERR_NETWORK_CHANGED" in err_str or "net::ERR_INTERNET_DISCONNECTED" in err_str:
                print("⚠ Internet lost. Waiting to reconnect...")
                wait_for_internet()
                try:
                    page.reload(timeout=timeout, wait_until="domcontentloaded")
                    page.wait_for_load_state("load", timeout=30000)
                    return True
                except Exception as reload_error:
                    print(f"Reload failed: {reload_error}")
            elif "Timeout" in err_str:
                console.print(f"[yellow]Timeout (attempt {attempt}/{MAX_NAV_ATTEMPTS}). Will skip this URL if all retries fail.[/yellow]")
            else:
                print(f"Unexpected error. Retrying... ({e})")

            if attempt >= MAX_NAV_ATTEMPTS:
                console.print(f"[red]Nag-timeout o nag-fail pagkatapos ng {MAX_NAV_ATTEMPTS} attempts. Skipping this URL.[/red]")
                return False
            time.sleep(5)
            attempt += 1
    return False