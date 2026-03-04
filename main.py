import sys
import warnings
warnings.filterwarnings("ignore", message=".*urllib3.*chardet.*")
from utils import is_internet_available
from scraper import scrape_all


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].strip().lower() in ("--manual", "-m", "manual"):
        from run_manual import main as manual_main
        manual_main()
    elif is_internet_available():
        scrape_all()
    else:
        print("No internet connection found.\nExiting...")