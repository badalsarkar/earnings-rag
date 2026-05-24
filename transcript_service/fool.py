"""Motley Fool URL construction and transcript scraping."""
import requests
from bs4 import BeautifulSoup

FOOL_BASE = "https://www.fool.com/earnings/call-transcripts"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


_SUFFIXES = ("earnings-call-transcript", "earnings-transcript")


def build_transcript_url(
    company_slug: str, ticker: str, quarter: int, year: int, report_date: str,
    suffix: str = _SUFFIXES[0],
) -> str:
    """Construct the Motley Fool transcript URL without any network check."""
    ticker_lower = ticker.lower()
    return f"{FOOL_BASE}/{report_date}/{company_slug}-{ticker_lower}-q{quarter}-{year}-{suffix}/"


def scrape_transcript(url: str) -> str:
    response = requests.get(url, headers=_HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    article = soup.find("div", class_="article-body") or soup.find("article")
    if not article:
        raise ValueError(f"Could not find article content at {url}")

    paragraphs = article.find_all("p")
    return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))