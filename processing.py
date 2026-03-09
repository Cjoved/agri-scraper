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


def _process_one_sheet(data, sheet_name, commodity_type, unwanted_texts, log_prefix="", selected_commodity_labels=None):
    """
    Core logic: turn one Excel sheet into cleaned long-format DataFrame.
    Layout base: OpenStat export tulad ng 2M4AFN01.xlsx
      - Row 0: title (skip)
      - Row 1: blank (skip)
      - Row 2: year row (e.g. 2010) sa columns 2+
      - Row 3: month row (January, February, ...) sa columns 2+
      - Row 4+: Column 0 = Geolocation, Column 1 = Commodity (Palay, Corngrain, etc.), Column 2+ = price cells
    Ang gusto natin: Commodity = talagang galing sa column 1 (specific names), hindi category lang na "Cereals".
    """
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

    year_ser = (
        data.iloc[year_row_index, 2:]
        .astype(str)
        .str.extract(r"(\d{4})", expand=False)
    )
    year_ser = year_ser.ffill().bfill()
    year_headers = year_ser.astype(int).values
    month_row_index = year_row_index + 1
    months_raw = (
        data.iloc[month_row_index, 2:]
        if month_row_index < len(data)
        else pd.Series(dtype=object)
    )
    months = months_raw.astype(str).str.strip().replace({"": np.nan, "nan": np.nan})
    # Kung header ay "2016 January", kunin lang "January" para sa Period
    def _month_only(v):
        s = str(v).strip()
        if not s or s == "nan":
            return np.nan
        parts = s.split()
        if len(parts) > 1 and parts[-1].isalpha():
            return parts[-1]
        return s
    months = months.apply(_month_only).values
    n_val_cols = len(data.columns) - 2
    if len(year_headers) < n_val_cols:
        year_headers = np.resize(year_headers, n_val_cols)
    if len(months) < n_val_cols:
        months = np.resize(months, n_val_cols)
    if not len(year_headers) or n_val_cols == 0:
        print(f"{log_prefix}Insufficient temporal data in sheet {sheet_name}")
        return None

    year_col_map = list(year_headers[:n_val_cols])
    months = list(months[:n_val_cols]) if hasattr(months, "__len__") else months

    data = data.iloc[month_row_index + 1:].reset_index(drop=True)
    data.rename(columns={0: "Geolocation", 1: "Commodity"}, inplace=True)

    # 1) Detect if column 1 is actually a category-only field (e.g., "Cereals" repeated)
    comm_col = data["Commodity"].astype(str).str.strip().replace({"": np.nan, "nan": np.nan}).dropna()
    comm_uniques = comm_col.unique().tolist()

    KNOWN_TYPES = {
        "Beans and Legumes", "Cereals", "Commercial Crops", "Condiments",
        "Fruit Vegetables", "Fruits", "Leafy Vegetables", "Livestock",
        "Poultry", "Rootcrops"
    }

 # Detect if column "Commodity" is actually just a category/type (e.g., "Cereals" repeated)
    valid = []
    for x in comm_uniques:
        x2 = str(x).strip()
        if x2 in KNOWN_TYPES:
            valid.append(x2)
        elif x2 in {"Cereal"}:  # optional alias handling
            valid.append("Cereals")

# If the column contains only known category/type values (max 2 variants), treat it as Commodity Type
    if comm_uniques and len(valid) == len(comm_uniques) and len(comm_uniques) <= 2:
        commodity_type = valid[0]

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
    # Base sa 2M4AFN01.xlsx: column 1 = tunay na Commodity (Palay, Corngrain, Green Corn, etc.). Huwag palitan kung may ganyan na.
    # Palitan lang kung talagang category lang ang laman (Cereals/Cereal lang, walang specific names).
    comm_str = data_long["Commodity"].astype(str).str.strip()
    comm_unique = comm_str.replace("", np.nan).dropna().unique().tolist()
    comm_unique = [c for c in comm_unique if c and c != "nan"]
    # Huwag ituring na "real" kung exactong "Cereals"/"Cereal" lang (category, hindi specific name)
    is_strictly_cereal_category = all(
        c in ("Cereals", "Cereal") for c in comm_unique
    )
    has_real_commodity_names = not is_strictly_cereal_category and any(
        ("Palay" in c or "Corngrain" in c or "Green Corn" in c or "Maize" in c or "[" in c or len(c) > 20)
        for c in comm_unique
    )
    is_cereal_only = (len(comm_unique) <= 2 and is_strictly_cereal_category) or (
        len(comm_unique) <= 1 and (not comm_unique or comm_unique[0] in ("Cereals", "Cereal"))
    )
    if is_cereal_only:
        # Gamitin: una ang selected labels mula sa page (Palay, Corngrain, etc.), kung wala sheet name
        replacement = None
        if selected_commodity_labels:
            labels = [str(l).strip() for l in selected_commodity_labels if l and str(l).strip()]
            if len(labels) == 1:
                replacement = labels[0]
            elif labels:
                replacement = ", ".join(labels[:5])  # max 5 para hindi masyadong mahaba
        if not replacement and sheet_name and str(sheet_name).strip():
            replacement = str(sheet_name).strip()
        if replacement:
            data_long["Commodity"] = replacement
            print(f"{log_prefix}Commodity was category only (Cereals); using: {replacement[:50]}...")
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
    data_long["Month"] = data_long["column_index"].apply(
        lambda x: months[x - 2] if x - 2 < len(months) else None
    )
    data_long.drop(columns=["column_index"], inplace=True)

    data_long["Price"] = data_long["Price"].astype(str).str.strip()
    # Tanggalin ang anumang nakadugtong na "Cereals" o ibang known type sa Price (dapat numeric lang)
    for k in KNOWN_TYPES:
        data_long["Price"] = data_long["Price"].str.replace(r"\s*" + re.escape(k) + r"\s*$", "", regex=True)
    data_long["Price"] = data_long["Price"].replace(["..", "-", "NA", ""], np.nan)
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

    # Impute per commodity using a loop (pandas 3.0-safe — groupby+apply drops key column)
    for comm_val, idx in data_long.groupby("Commodity").groups.items():
        subset = data_long.loc[idx, ["Price"]]
        if subset["Price"].notna().sum() == 0:
            print(f"{log_prefix}No historical data for {comm_val}. Skipping imputation.")
            continue
        try:
            imputer = SimpleImputer(strategy="mean")
            data_long.loc[idx, "Price"] = imputer.fit_transform(subset).round(2)
        except Exception as e:
            print(f"{log_prefix}Imputation failed for {comm_val}: {e}!")
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
def download_and_process_excel(page, url_index, timestamp, urls, selected_commodity_labels=None):
    print(f"Downloading Excel file for URL {url_index + 1}/{len(urls)}...")
    selected_commodity_labels = selected_commodity_labels or []

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
                log_prefix=f"URL {url_index + 1} ",
                selected_commodity_labels=selected_commodity_labels,
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