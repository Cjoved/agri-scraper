import io
import os
import re
import glob
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from utils import require_internet
from sklearn.impute import SimpleImputer

load_dotenv()

# Folder kung saan ilalagay ang manually downloaded Excel files (kapag blocked ng Cloudflare)
# Laging nasa project folder, kahit saan mo i-run ang script
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MANUAL_DOWNLOADS_FOLDER = os.path.join(_PROJECT_DIR, "manual_downloads")


def _process_one_sheet(data, sheet_name, commodity_type, unwanted_texts, log_prefix=""):
    """Core logic: turn one Excel sheet into cleaned long-format DataFrame."""
    data = data.copy()
    data.dropna(how="all", inplace=True)
    if data.empty:
        print(f"{log_prefix}Sheet {sheet_name} is empty after dropping NA rows")
        return None
    data.reset_index(drop=True, inplace=True)

    possible_year_row = data.iloc[:5].apply(
        lambda row: row.astype(str).str.contains(r"\d{4}").sum(), axis=1
    )
    year_row_index = (
        possible_year_row.idxmax() if possible_year_row.max() > 0 else None
    )
    if year_row_index is None:
        print(f"{log_prefix}No year row detected in sheet {sheet_name}")
        return None

    year_headers = (
        data.iloc[year_row_index, 2:]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
        .ffill()
        .dropna()
        .astype(int)
        .values
    )
    month_row_index = year_row_index + 1
    months = (
        data.iloc[month_row_index, 2:].dropna().astype(str).values
        if month_row_index is not None and month_row_index < len(data)
        else []
    )
    if not len(year_headers) or not len(months):
        print(f"{log_prefix}Insufficient temporal data in sheet {sheet_name}")
        return None

    year_col_map = []
    for i, month in enumerate(months):
        if i < len(year_headers):
            year_col_map.append(year_headers[i])

    data = data.iloc[month_row_index + 1:].reset_index(drop=True)
    data.rename(columns={0: "Geolocation", 1: "Commodity"}, inplace=True)

    try:
        data_long = pd.melt(
            data,
            id_vars=["Geolocation", "Commodity"],
            var_name="column_index",
            value_name="Price",
        )
    except Exception as e:
        print(f"{log_prefix}Failed to melt data for sheet {sheet_name}: {e}")
        return None

    data_long["Commodity Type"] = commodity_type
    # Kung blank pa rin ang Commodity, ibig sabihin mali ang export layout (hindi naka-'Beginning of row')
    if data_long["Commodity"].astype(str).str.strip().eq("").all() or data_long["Commodity"].isna().all():
        print(
            f"{log_prefix}ERROR: Commodity column is blank in sheet {sheet_name}. "
            "Malamang hindi naka-tick ang 'Beginning of row' para sa Commodity/Geolocation/Period."
        )
        return None
    data_long["Year"] = data_long["column_index"].apply(
        lambda x: year_col_map[x - 2] if x - 2 < len(year_col_map) else None
    )
    data_long["Period"] = data_long["column_index"].apply(
        lambda x: months[x - 2] if x - 2 < len(months) else None
    )
    data_long.drop(columns=["column_index"], inplace=True)

    data_long["Price"] = data_long["Price"].replace(["..", "-", "NA"], "")
    pattern = "|".join(map(re.escape, unwanted_texts))
    data_long = data_long[
        ~data_long.astype(str).apply(
            lambda row: row.str.contains(pattern, na=False, regex=True).any(),
            axis=1,
        )
    ]

    data_long["Geolocation"] = (
        data_long["Geolocation"]
        .str.replace(r"^\.+", "", regex=True)
        .replace("", np.nan)
        .ffill()
    )
    if data_long[["Geolocation", "Commodity"]].isna().all().all():
        print(f"{log_prefix}No valid geolocation/commodity data in sheet {sheet_name}")
        return None
    data_long.dropna(subset=["Geolocation", "Commodity"], inplace=True)

    data_long["Price"] = pd.to_numeric(data_long["Price"], errors="coerce")
    data_long.columns = data_long.columns.astype(str)
    data_long[["Geolocation", "Commodity"]] = data_long[
        ["Geolocation", "Commodity"]
    ].fillna("")

    def impute_prices(group):
        if group["Price"].notna().sum() == 0:
            print(
                f"{log_prefix}No historical data for {group['Commodity'].iloc[0]}. Skipping imputation."
            )
            return group
        try:
            imputer = SimpleImputer(strategy="mean")
            group.loc[:, "Price"] = imputer.fit_transform(group[["Price"]])
            group.loc[:, "Price"] = group["Price"].round(2)
        except Exception as e:
            print(f"{log_prefix}Imputation failed for {group['Commodity'].iloc[0]}: {e}!")
        return group

    data_long = (
        data_long.groupby(
            "Commodity", group_keys=False, observed=True, as_index=False
        )
        .apply(impute_prices)
        .reset_index(drop=True)
    )
    return data_long


def process_excel_from_path(file_path, commodity_type="Commodity"):
    """Process one Excel file from disk (walang browser). Para sa manual download mode."""
    unwanted_texts = os.getenv("UNWANTED_TEXTS", "").split(",")
    try:
        df = pd.read_excel(file_path, sheet_name=None, header=None)
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
        return pd.DataFrame()

    all_data = []
    for sheet_name, data in df.items():
        if data is None or data.empty:
            continue
        result = _process_one_sheet(
            data, sheet_name, commodity_type, unwanted_texts,
            log_prefix=f"[{os.path.basename(file_path)}] "
        )
        if result is not None:
            all_data.append(result)
            print(f"Processed {file_path}, sheet {sheet_name}")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def process_manual_downloads(folder=None):
    """
    Process lahat ng Excel files sa folder (manual_downloads by default).
    Returns combined DataFrame. Walang internet/browser na kailangan.
    """
    folder = folder or MANUAL_DOWNLOADS_FOLDER
    os.makedirs(folder, exist_ok=True)
    patterns = [os.path.join(folder, "*.xlsx"), os.path.join(folder, "*.xls")]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    files = sorted(set(files))

    if not files:
        print(f"Walang .xlsx o .xls na file sa folder: {os.path.abspath(folder)}")
        print("Ilagay mo muna ang na-download na Excel files mula sa OpenSTAT (sa normal browser).")
        return pd.DataFrame()

    print(f"Found {len(files)} file(s). Processing...")
    frames = []
    for path in files:
        # Optional: commodity type mula sa filename, e.g. "Cereals_001.xlsx" -> "Cereals"
        base = os.path.basename(path)
        if "_" in base and not base.startswith("_"):
            commodity_type = base.split("_")[0].strip()
        else:
            commodity_type = "Commodity"
        df = process_excel_from_path(path, commodity_type=commodity_type)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


@require_internet
def download_and_process_excel(page, url_index, timestamp, urls):
    print(f"Downloading Excel file for URL {url_index + 1}/{len(urls)}...")

    # Enhanced timeout and retry configuration
    MAX_SUBMIT_RETRIES = 3
    BASE_TIMEOUT = 300000  # 5 minutes
    INCREMENTAL_TIMEOUT = url_index * 30000  # 30 seconds more per URL
    TOTAL_TIMEOUT = min(BASE_TIMEOUT + INCREMENTAL_TIMEOUT, 600000)  # Max 10 minutes

    # Ensure error directories exist
    os.makedirs("screenshots", exist_ok=True)
    os.makedirs("error_logs", exist_ok=True)

    try:
        for attempt in range(MAX_SUBMIT_RETRIES):
            try:
                print(f"Attempt {attempt + 1}/{MAX_SUBMIT_RETRIES} to submit and download...")

                with page.expect_download(timeout=TOTAL_TIMEOUT) as download_info:
                    # Enhanced click with timeout and verification
                    page.click("input[type='submit']", timeout=30000)

                download = download_info.value

                # Verify download completion
                download_path = download.path()
                wait_time = 0
                while not os.path.exists(download_path) and wait_time < 120:  # Max 2 minutes
                    page.wait_for_timeout(1000)
                    wait_time += 1

                if not os.path.exists(download_path):
                    raise Exception("Download file not found after waiting")

                print("File downloaded successfully!, analyzing file...")
                break  # Exit retry loop if successful

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == MAX_SUBMIT_RETRIES - 1:
                    # Final attempt failed, capture diagnostics
                    print("Failed to submit after multiple attempts. Capturing diagnostics...")
                    page.screenshot(path=f"screenshots/failure_url_{url_index + 1}.png")
                    with open(f"error_logs/url_{url_index + 1}.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    return {}  # Return empty dict to skip this URL

                # Wait before retrying with increasing delay
                retry_delay = (attempt + 1) * 5000  # 5, 10, 15 seconds
                print(f"Retrying in {retry_delay / 1000} seconds...")
                page.wait_for_timeout(retry_delay)

        # Proceed with reading and processing Excel content
        file_stream = io.BytesIO()
        with open(download.path(), "rb") as f:
            file_stream.write(f.read())
        file_stream.seek(0)

        print("...Reading and cleaning Excel content...")
        df = pd.read_excel(file_stream, sheet_name=None, header=None)
        unwanted_texts = os.getenv("UNWANTED_TEXTS").split(",")

        def get_commodity_type_from_page(page):
            try:
                title_text = page.text_content(
                    "span.hierarchical_tableinformation_title",
                    timeout=10000
                ).strip()
                commodity_type = title_text.split(":")[0]
                return commodity_type[:20]
            except Exception as e:
                print(f"Could not extract commodity name: {e}!")
                return f"Commodity_{url_index}"

        commodity_type = get_commodity_type_from_page(page)
        all_data = []
        for sheet, data in df.items():
            if data is None or data.empty:
                continue
            result = _process_one_sheet(
                data, sheet, commodity_type, unwanted_texts,
                log_prefix=f"URL {url_index + 1} "
            )
            if result is not None:
                all_data.append(result)
                print(f"Processed data from URL {url_index + 1}, sheet {sheet}")

        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return combined_df
        return pd.DataFrame()

    except Exception as e:
        print(f"Critical error processing URL {url_index + 1}: {str(e)}")
        return pd.DataFrame()
