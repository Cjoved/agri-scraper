#  Agricultural Commodities' Price Scraper
---

**Dataset Description:**  
This dataset contains scraped and processed agricultural commodity price data from PSA's website (OpenSTAT). The data is gathered per region, commodity type, and period (month or annual), and saved in a cleaned, structured CSV file.

---

##  Columns:

| Column Name       | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| `Geolocation`     | The region or province where the data was collected.                       |
| `Commodity`       | The specific agricultural product (e.g., "Tomato", "Rice").                |
| `Commodity Type`  | The category of the commodity (e.g., "Vegetables", "Cereals").             |
| `Year`            | The year corresponding to the price value.                                 |
| `Period`          | The month or time period within the year (e.g., "January", "Annual").      |
| `Price`           | The average price of the commodity for the given region and time period.   |

---

## Setup & Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install
```
2. Make sure that the .env file contents match the MySQL database credentials you're using.
   
3. Run the scraper:
```py
python main.py
```

### Cloudflare bypass (openstat.psa.gov.ph)

Kung na-block ng Cloudflare "Performing security verification", may dalawang paraan para ma-bypass:

**Option A – FlareSolverr (recommended, ~90% success)**  
1. Install [Docker](https://docs.docker.com/get-docker/).  
2. I-run ang FlareSolverr:
```bash
docker run -d --name flaresolverr -p 8191:8191 -e LOG_LEVEL=info --restart unless-stopped ghcr.io/flaresolverr/flaresolverr:latest
```
3. Sa `.env` idagdag:
```
FLARESOLVERR_URL=http://localhost:8191
```
4. Run ulit: `python main.py`. Kokopyahin ng script ang cookies mula sa FlareSolverr papunta sa browser.

**Option B – curl_cffi (TLS fingerprint)**  
Naka-include na sa `requirements.txt`. Kung hindi mo gagamitin FlareSolverr, susubukan ng script ang `curl_cffi` para kunin ang cookies (Chrome impersonation). Minsan sapat na ito para makalusot.

**Option C – Manual mode**  
Kung hindi pa rin makalusot: mag-download ng Excel sa **normal browser** (Chrome/Edge), ilagay ang mga file sa folder na `manual_downloads`, tapos:
```bash
python run_manual.py
```

---

##  Cleaning Process:

- Dropped all rows and columns that are entirely empty (`NaN`).
- Removed rows containing user-defined unwanted patterns from the `.env` file (see `UNWANTED_TEXTS`).

---

##  Imputation Process:

- For commodities with missing price data:
  - We **group by each commodity**.
  - If the group contains at least one valid price, we use **mean imputation** to fill in the missing values (`NaN`) in the `Price` column.
  - This is done using `SimpleImputer(strategy='mean')` from `sklearn.impute`.
  - Prices are rounded to 2 decimal places after imputation.

>  If a commodity group contains **no historical data (i.e., all values missing)**, we skip imputation for that group.

---

##  Example Data Preview:

| Geolocation | Commodity | Price | Commodity Type   | Year    | Period   |
|-------------|-----------|-------|------------------|---------|----------|
| Abra        | Avocado   | 300   | Fruits           | 2023    | January  |
| Apayao      | Beans     | 50.75 | Beans and Legumes| 2024    | February |
| Benguet     | Corn      | 150   | Cereals          | 2025    | Annual   |

---

##  File Output:

- The cleaned data is saved as separate .csv files by Commodity, such as:  
  **`CommodityName_<timestamp>.csv`**  
  Located in:  
  **Desktop/Agri-Price-Data_Files/**

## Sample Output:
```bash
https://drive.google.com/drive/folders/1sN-CUXZVF8rUzO69IAzZ1HkfHUdCynlT?usp=sharing
```
