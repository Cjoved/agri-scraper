from playwright.sync_api import sync_playwright
from utils import require_internet, wait_for_selector_with_retry, wait_for_internet
from processing import download_and_process_excel
from database import store_data_in_mysql
from dotenv import load_dotenv
from rich.console import Console
from datetime import datetime
import os
import pandas as pd
import time

try:
    from cloudflare_bypass import get_cloudflare_cookies
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

        for url_index, url in enumerate(urls):
            console.rule(f"[bold green]Processing URL {url_index + 1}/{len(urls)}")
            navigate_with_retries(page, url)
            wait_for_cloudflare_check(page, url_index)

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

            remaining_years = list(range(total_years))

            while remaining_years:
                current_batch = []
                for year_idx in remaining_years:
                    test_batch = current_batch + [year_idx]
                    console.print(f"[dim]Testing batch:[/dim] {test_batch}")

                    navigate_with_retries(page, url)
                    wait_for_cloudflare_check(page, url_index)
                    select_dropdown_options(page, test_batch)

                    try:
                        is_error = page.is_visible(
                            "#ctl00_ContentPlaceHolderMain_VariableSelector1_VariableSelector1_SelectionErrorlabel",
                            timeout=5000
                        )
                        if is_error:
                            console.print("[yellow]Selection limit hit, finalizing batch...[/yellow]")
                            break
                        else:
                            current_batch = test_batch
                    except Exception as e:
                        console.print(f"[red]Error checking selection: {e}[/red]")
                        break

                if not current_batch:
                    skipped = remaining_years.pop(0)
                    console.print(f"[red]Skipped year index:[/red] {skipped}")
                    continue

                # Finalize dropdowns and download
                try:
                    navigate_with_retries(page, url)
                except Exception as nav_err:
                    console.print(f"[red]Navigate failed after {MAX_NAV_ATTEMPTS} attempts. Skipping batch {current_batch}.[/red]")
                    remaining_years = [y for y in remaining_years if y not in current_batch]
                    continue
                wait_for_cloudflare_check(page, url_index)
                select_dropdown_options(page, current_batch, finalize=True)

                try:
                    submit_button = page.wait_for_selector("input[type='submit']", timeout=120000)
                    submit_button.click()
                    # "load" lang para hindi ma-stuck sa networkidle (mabigat ang OpenSTAT)
                    page.wait_for_load_state("load", timeout=90000)

                    cleaned_data = download_and_process_excel(page, url_index, timestamp, urls)
                    if not cleaned_data.empty:
                        all_data_frames.append(cleaned_data)
                        console.print(f"[green]✔ Processed batch:[/green] {current_batch}")
                    else:
                        console.print("[yellow]No data returned[/yellow]")

                except Exception as e:
                    console.print(f"[red] Submission error:[/red] {e}")

                remaining_years = [y for y in remaining_years if y not in current_batch]

        browser.close()

    if all_data_frames:
        final_df = pd.concat(all_data_frames, ignore_index=True)
        # Siguraduhing may Commodity column para makita ng supervisor (Rice, Cereals, etc.)
        if "Commodity" not in final_df.columns:
            final_df["Commodity"] = final_df.get("Commodity Type", "N/A")
        # Ayos ng column order: Geolocation, Commodity, Price, Commodity Type, Year, Period
        col_order = ["Geolocation", "Commodity", "Price", "Commodity Type", "Year", "Period"]
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
    """Navigate to a URL, retrying on errors. Max MAX_NAV_ATTEMPTS tries para hindi ma-stuck."""
    attempt = 1
    while attempt <= MAX_NAV_ATTEMPTS:
        try:
            print(f"→ Navigating to URL (Attempt {attempt}/{MAX_NAV_ATTEMPTS})...")
            page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            # "load" sapat na; "networkidle" minsan hindi umabot sa mabigat na page
            page.wait_for_load_state("load", timeout=30000)
            return
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
                    return
                except Exception as reload_error:
                    print(f"Reload failed: {reload_error}")
            elif "Timeout" in err_str:
                console.print(f"[yellow]Timeout (attempt {attempt}/{MAX_NAV_ATTEMPTS}). Subukan ulit o mag-manual mode.[/yellow]")
            else:
                print(f"Unexpected error. Retrying... ({e})")

            if attempt >= MAX_NAV_ATTEMPTS:
                console.print(f"[red]Nag-timeout o nag-fail pagkatapos ng {MAX_NAV_ATTEMPTS} attempts. Skip o manual mode.[/red]")
                raise
            time.sleep(5)
            attempt += 1

    