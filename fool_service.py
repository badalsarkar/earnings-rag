import re
import requests
from bs4 import BeautifulSoup

FOOL_BASE_URL = "https://www.fool.com/earnings/call-transcripts"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get_earnings_transcript(ticker: str, quarter: int, year: int, url: str | None = None) -> str:
    """Fetch an earnings call transcript from The Motley Fool.

    If `url` is provided, scrapes that page directly.
    Otherwise, attempts auto-discovery via Yahoo Finance earnings dates.
    """
    if url is None:
        url = _find_transcript_url(ticker, quarter, year)
    return scrape_transcript(url)


def scrape_transcript(url: str) -> str:
    """Scrape a transcript from a Motley Fool earnings call transcript URL."""
    response = requests.get(url, headers=_HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    article = soup.find("div", class_="article-body") or soup.find("article")
    if not article:
        raise ValueError(f"Could not find article content at {url}")

    paragraphs = article.find_all("p")
    return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))


def _find_transcript_url(ticker: str, quarter: int, year: int) -> str:
    """Attempt to find the Motley Fool transcript URL via Yahoo Finance earnings dates."""
    date = _get_earnings_date(ticker, quarter, year)
    company_slug = _get_company_slug(ticker)
    ticker_lower = ticker.lower()

    # Motley Fool URL pattern: YYYY/MM/DD/{company}-{ticker}-q{q}-{year}-earnings-call-transcript/
    url = (
        f"{FOOL_BASE_URL}/{date.replace('-', '/')}/"
        f"{company_slug}-{ticker_lower}-q{quarter}-{year}-earnings-call-transcript/"
    )
    resp = requests.head(url, headers=_HEADERS, timeout=10, allow_redirects=True)
    if resp.status_code == 200:
        return url

    # Try alternate slug (some transcripts use "-earnings-transcript/" without "call-")
    url_alt = url.replace("-earnings-call-transcript/", "-earnings-transcript/")
    resp = requests.head(url_alt, headers=_HEADERS, timeout=10, allow_redirects=True)
    if resp.status_code == 200:
        return url_alt

    raise ValueError(
        f"Could not auto-discover transcript URL for {ticker} Q{quarter} {year}. "
        f"Pass the URL directly: get_earnings_transcript('{ticker}', {quarter}, {year}, url='...'). "
        f"Find it at https://www.fool.com/earnings-call-transcripts/?ticker={ticker}"
    )


def _get_earnings_date(ticker: str, quarter: int, year: int) -> str:
    """Get the earnings call date from Yahoo Finance calendar events (YYYY-MM-DD)."""
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
    resp = requests.get(
        url,
        params={"modules": "calendarEvents"},
        headers={**_HEADERS, "Accept": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    earnings_dates = (
        data.get("quoteSummary", {})
        .get("result", [{}])[0]
        .get("calendarEvents", {})
        .get("earnings", {})
        .get("earningsDate", [])
    )
    if earnings_dates:
        from datetime import datetime
        ts = earnings_dates[0].get("raw", 0)
        return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
    raise ValueError(f"Could not get earnings date for {ticker} from Yahoo Finance")


def _get_company_slug(ticker: str) -> str:
    """Get the URL-safe company name slug from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
    resp = requests.get(
        url,
        params={"modules": "quoteType"},
        headers={**_HEADERS, "Accept": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    name = (
        data.get("quoteSummary", {})
        .get("result", [{}])[0]
        .get("quoteType", {})
        .get("longName", ticker)
    )
    # Slugify: lowercase, replace non-alphanumeric with hyphens, strip trailing hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug
