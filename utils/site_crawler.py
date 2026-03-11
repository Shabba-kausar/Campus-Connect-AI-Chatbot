import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time

def collect_site_urls(start_url: str, domain: str = None, keywords=None, max_pages: int = 300, delay: float = 0.5):
    """Crawl start_url (breadth-first) and collect internal links matching keywords.

    Returns a dict mapping keyword -> url (first discovered URL containing the keyword).
    """
    if keywords is None:
        keywords = ["admission", "admissions", "course", "courses", "hostel", "library", "placement", "placements", "training", "facility", "facilities", "news", "about", "contact"]

    parsed = urlparse(start_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if domain is None:
        domain = parsed.netloc

    seen = set()
    queue = [start_url]
    results = {}
    pages = 0

    headers = {"User-Agent": "MANUU-Site-Crawler/1.0 (+https://example.com)"}

    while queue and pages < max_pages and len(results) < len(keywords):
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            pages += 1
            time.sleep(delay)

            # extract links
            for a in soup.find_all('a', href=True):
                href = a['href']
                # normalize
                full = urljoin(base, href)
                p = urlparse(full)
                if p.netloc.endswith(domain):
                    # avoid fragments
                    full = full.split('#')[0]
                    if full not in seen and full not in queue:
                        queue.append(full)

                    # match keywords in path
                    path_lower = p.path.lower()
                    for kw in keywords:
                        if kw in path_lower and kw not in results:
                            results[kw] = full
            # also try to match on page text for keywords
            page_text = soup.get_text(' ', strip=True).lower()
            for kw in keywords:
                if kw in page_text and kw not in results:
                    results[kw] = url

        except Exception:
            # ignore fetch errors and continue
            continue

    # Normalize results to a compact mapping for known keys
    mapping = {}
    key_aliases = {
        'admission': ['admission', 'admissions'],
        'courses': ['course', 'courses', 'academic'],
        'hostel': ['hostel'],
        'library': ['library'],
        'training_placement': ['placement', 'placements', 'training'],
        'facilities': ['facility', 'facilities'],
        'about': ['about'],
        'contact': ['contact']
    }
    for norm, aliases in key_aliases.items():
        for a in aliases:
            if a in results:
                mapping[norm] = results[a]
                break

    return mapping

def save_mapping(mapping: dict, out_path: str):
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2)
