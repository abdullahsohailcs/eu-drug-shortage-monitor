"""Shared settings for the EU drug shortage scrapers.

Output files go to ./output next to these scripts, unless the OUTPUT_DIR
environment variable points somewhere else.
"""
import os
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", Path(__file__).resolve().parent / "output"))

# Seconds to wait between page requests, to keep the load on public sites low.
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.5"))


def output_path(country: str, kind: str = "shortages", ext: str = "xlsx") -> str:
    """Return a dated output path, e.g. output/belgium_shortages_2026-10-29.xlsx."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    return str(OUTPUT_DIR / f"{country}_{kind}_{date}.{ext}")
