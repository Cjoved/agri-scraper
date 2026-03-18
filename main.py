"""
Main entry: isa lang pwedeng tumakbo bawat run (PhilRice, PhilRice News, PinoyRice, OpenSTAT, o IRRI).
Control via .env: PHILRICE, PHILRICE_NEWS, PINOYRICE, OPENSTAT, IRRI (true/false).
- PHILRICE=true: PhilRice PDF scrape -> process only.
- PHILRICE_NEWS=true: PhilRice News scrape -> process only (bukod sa PhilRice PDF).
- PINOYRICE=true: PinoyRice scrape (text + PDF) -> pinoyrice_corpus.jsonl.
- OPENSTAT=true: OpenSTAT scrape.
- IRRI=true: IRRI Philippines scrape (text + PDFs) -> data/irri_processed/text, data/irri_pdfs.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _philrice_enabled() -> bool:
    v = (os.getenv("PHILRICE") or "false").strip().lower()
    return v in ("true", "1", "yes")


def _pinoyrice_enabled() -> bool:
    v = (os.getenv("PINOYRICE") or "false").strip().lower()
    return v in ("true", "1", "yes")


def _philrice_news_enabled() -> bool:
    v = (os.getenv("PHILRICE_NEWS") or "false").strip().lower()
    return v in ("true", "1", "yes")


def _openstat_enabled() -> bool:
    v = (os.getenv("OPENSTAT") or "true").strip().lower()
    return v in ("true", "1", "yes")


def _irri_enabled() -> bool:
    v = (os.getenv("IRRI") or "false").strip().lower()
    return v in ("true", "1", "yes")


def main():
    from rich.console import Console
    console = Console()

    console.rule("[bold]Main – PhilRice / PhilRice News / PinoyRice / OpenSTAT / IRRI (isa lang per run)[/bold]")
    philrice = _philrice_enabled()
    philrice_news = _philrice_news_enabled()
    pinoyrice = _pinoyrice_enabled()
    openstat = _openstat_enabled()
    irri = _irri_enabled()
    console.print(f"[dim]PHILRICE={os.getenv('PHILRICE', 'false')}  PHILRICE_NEWS={os.getenv('PHILRICE_NEWS', 'false')}  PINOYRICE={os.getenv('PINOYRICE', 'false')}  OPENSTAT={os.getenv('OPENSTAT', 'true')}  IRRI={os.getenv('IRRI', 'false')}[/dim]")

    if philrice and (philrice_news or pinoyrice or openstat or irri):
        console.print("[yellow]PhilRice (PDF) uuna (isa lang per run).[/yellow]")
        philrice_news = pinoyrice = openstat = irri = False
    elif philrice_news and (pinoyrice or openstat or irri):
        console.print("[yellow]PhilRice News uuna.[/yellow]")
        pinoyrice = openstat = irri = False
    elif pinoyrice and (openstat or irri):
        console.print("[yellow]PinoyRice uuna.[/yellow]")
        openstat = irri = False
    elif openstat and irri:
        console.print("[yellow]OpenSTAT uuna.[/yellow]")
        irri = False

    if philrice:
        console.rule("[bold cyan]PhilRice – PDF Scrape[/bold cyan]")
        from src.scrapers import philrice as scraper_philrice
        scraper_philrice.run()
        console.rule("[bold cyan]PhilRice – PDF Process (clean -> JSONL)[/bold cyan]")
        from src.services import philrice as processing_philrice
        processing_philrice.run()
    elif philrice_news:
        console.rule("[bold cyan]PhilRice News – Scrape[/bold cyan]")
        from src.scrapers import philrice_news as scraper_philrice_news
        scraper_philrice_news.run()
        console.rule("[bold cyan]PhilRice News – Process (.txt -> CPT JSON)[/bold cyan]")
        from src.services import philrice_news as processing_philrice_news
        processing_philrice_news.run()
    elif pinoyrice:
        console.rule("[bold cyan]PinoyRice – Scrape (text + PDF)[/bold cyan]")
        from src.scrapers import pinoyrice as scraper_pinoyrice
        scraper_pinoyrice.run()
    elif openstat:
        console.rule("[bold cyan]OpenSTAT – Scrape[/bold cyan]")
        from src.scrapers import openstat as openstat_scraper
        openstat_scraper.scrape_all()
    elif irri:
        console.rule("[bold cyan]IRRI Philippines – Scrape (text + PDFs)[/bold cyan]")
        from src.scrapers import irri as irri_scraper
        irri_scraper.run()
        console.rule("[bold cyan]IRRI – Process (.txt → CPT JSON)[/bold cyan]")
        from src.services import irri as processing_irri
        processing_irri.run()
    else:
        console.print("[yellow]Set PHILRICE=true, PHILRICE_NEWS=true, PINOYRICE=true, OPENSTAT=true, o IRRI=true sa .env (isa lang per run).[/yellow]")

    console.rule("[bold green]Done[/bold green]")


if __name__ == "__main__":
    main()
