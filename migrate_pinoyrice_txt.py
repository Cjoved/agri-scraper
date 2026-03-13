"""
One-off helper script to move existing PinoyRice .txt files
from the old folder:
  pinoyrice_processed/per_file/*.txt
to the new dedicated raw-text folder:
  pinoyrice_txt/*.txt

Run once after the refactor:
  python migrate_pinoyrice_txt.py
"""
import os
import shutil
from pathlib import Path

from rich.console import Console

console = Console()

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OLD_DIR = os.path.join(PROJECT_DIR, "pinoyrice_processed", "per_file")
NEW_DIR = os.path.join(PROJECT_DIR, "pinoyrice_txt")


def run():
    console.rule("[bold cyan]Migrate PinoyRice .txt files")
    if not os.path.isdir(OLD_DIR):
        console.print(f"[yellow]Old folder not found: {OLD_DIR}[/yellow]")
        return
    os.makedirs(NEW_DIR, exist_ok=True)

    txt_files = sorted(Path(OLD_DIR).glob("*.txt"))
    if not txt_files:
        console.print(f"[yellow]No .txt files found in {OLD_DIR}[/yellow]")
        return

    moved = 0
    for src in txt_files:
        dst = Path(NEW_DIR) / src.name
        try:
            if dst.exists():
                console.print(f"[dim]Skip (exists): {dst.name}[/dim]")
                continue
            shutil.move(str(src), str(dst))
            moved += 1
        except Exception as e:
            console.print(f"[yellow]Could not move {src.name}: {e}[/yellow]")

    console.rule("[bold green]Done")
    console.print(f"Moved files: [green]{moved}[/green]")
    console.print(f"New folder: [cyan]{NEW_DIR}[/cyan]")


if __name__ == "__main__":
    run()

