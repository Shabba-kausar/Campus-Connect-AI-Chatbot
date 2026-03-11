import re
import time
from urllib.parse import urljoin, urlparse
from typing import List, Tuple, Optional, Dict, Set

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://manuu.edu.in/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0 Safari/537.36"
)


TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "admission process": ["admission", "apply", "application", "regular", "distance"],
    "hostel details": ["hostel", "boys hostel", "girls hostel", "accommodation", "mess"],
    "canteen": ["canteen", "cafeteria", "food", "mess"],
    "exam dates": ["examination", "exam", "time table", "timetable", "schedule", "notification"],
}

# Prefer direct URLs to avoid a crawl (much faster). These are stable entrypoints
# on the MANUU site; the crawler is used only as a fallback.
PREFERRED_URLS: Dict[str, str] = {
    "admission process": "https://manuu.edu.in/Admission",
    "hostel details": "https://manuu.edu.in/University/Students/Hostels",
    "canteen": "https://manuu.edu.in/University/Students/Facilities/Canteen",
    "exam dates": "https://manuu.edu.in/examination",
}

# Simple in-process cache with a soft TTL. Keeps responses instant for repeated
# clicks during a session.
_CACHE: Dict[str, Tuple[float, str, str]] = {}
_CACHE_TTL_SECONDS = 60 * 30  # 30 minutes


def _get(url: str) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        if resp.status_code != 200:
            return None
        return BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return None


def _extract_links(soup: BeautifulSoup, base: str) -> List[Tuple[str, str]]:
    links: List[Tuple[str, str]] = []
    for a in soup.find_all("a", href=True):
        text = (a.get_text(" ") or "").strip()
        href = a["href"].strip()
        # Normalize and keep only MANUU domain links
        href_abs = urljoin(base, href)
        if urlparse(href_abs).netloc.endswith("manuu.edu.in"):
            links.append((text, href_abs))
    return links


def _keyword_score(text: str, keywords: List[str]) -> int:
    text_lower = text.lower()
    score = 0
    for kw in keywords:
        if kw.lower() in text_lower:
            score += 1
    return score


def find_best_page_url(topic: str) -> Optional[str]:
    keywords = TOPIC_KEYWORDS.get(topic.lower(), [])
    # Fast path: use preferred URL if available
    pref = PREFERRED_URLS.get(topic.lower())
    if pref:
        return pref
    visited: Set[str] = set()
    queue: List[str] = [BASE_URL]

    best_url: Optional[str] = None
    best_score = -1

    # Limited breadth-first crawl (polite)
    steps = 0
    while queue and steps < 60:
        steps += 1
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        soup = _get(url)
        if not soup:
            continue

        # Score this page using its title and headings
        title = soup.title.get_text(strip=True) if soup.title else ""
        headings = " ".join(h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"]))
        page_text_for_score = f"{title} {headings}"
        score_here = _keyword_score(page_text_for_score, keywords)
        if score_here > best_score:
            best_score = score_here
            best_url = url

        # Enqueue children links selectively (prioritize likely sections)
        for text, href in _extract_links(soup, url):
            if any(kw in text.lower() for kw in keywords) or any(
                key in href.lower() for key in ["admission", "examin", "hostel", "canteen", "students", "notifications", "time-table", "time_table"]
            ):
                if href not in visited and href not in queue:
                    queue.append(href)

        # Be polite
        time.sleep(0.1)

    return best_url


def extract_main_text(url: str) -> str:
    soup = _get(url)
    if not soup:
        return ""
    # Prefer <main>, otherwise body text
    main = soup.find("main") or soup
    # Remove navigation/footer sections if possible
    for sel in ["nav", "header", "footer", "script", "style", "noscript"]:
        for tag in main.find_all(sel):
            tag.decompose()

    text = main.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_topic_detail(topic: str) -> Tuple[str, Optional[str]]:
    """
    Returns (text, source_url). If not found, text is empty.
    """
    # Cache check
    now = time.time()
    cached = _CACHE.get(topic.lower())
    if cached and (now - cached[0] < _CACHE_TTL_SECONDS):
        return cached[1], cached[2]

    url = find_best_page_url(topic)
    if not url:
        return "", None
    text = extract_main_text(url)
    # Store in cache
    _CACHE[topic.lower()] = (now, text, url)
    return text, url


def get_quick_action_answer(topic: str) -> Optional[str]:
    text, src = fetch_topic_detail(topic)
    if not text:
        return None
    # Keep it readable: trim overly long text but keep enough detail
    trimmed = text[:1800] + ("…" if len(text) > 1800 else "")
    header = topic.title()
    src_line = f"\n\nSource: {src}" if src else ""
    return f"{header}:\n{trimmed}{src_line}"


