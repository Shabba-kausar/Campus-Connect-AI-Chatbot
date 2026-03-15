import requests
from bs4 import BeautifulSoup
import re

# Enhanced fetcher that preserves structured data like tables and lists
# for the Heuristic Parser Fallback.

def fetch_from_web(url: str, max_chars: int = 5000) -> str | None:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        resp = requests.get(url, timeout=12, headers=headers)
        resp.raise_for_status()
        
        # Use lxml if available for speed, fallback to html.parser
        try:
            soup = BeautifulSoup(resp.text, 'lxml')
        except Exception:
            soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Remove noisy elements entirely
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe"]):
            tag.decompose()
        
        # Targeted content extraction
        main_body = soup.find('main') or soup.find('article') or soup.find(id='content') or soup.find(class_='content') or soup.body
        
        if not main_body:
            return None

        # Convert simple structural tags to text markers for the heuristic parser
        for br in main_body.find_all("br"):
            br.replace_with("\n")
        
        for li in main_body.find_all("li"):
            li.insert(0, "\n• ")
            
        for h in main_body.find_all(["h1", "h2", "h3", "h4"]):
            h.insert(0, "\n\n### ")
            h.append(" ###\n")

        # Table preservation logic
        for table in main_body.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                rows.append(" | ".join(cells))
            table.replace_with("\n" + "\n".join(rows) + "\n")

        text = main_body.get_text(separator=' ', strip=True)
        
        # Clean repetitive whitespace but keep newlines
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Noise reduction patterns specifically for MANUU site
        noise_patterns = [
            r'Skip to main content',
            r'Language Selection.*?(Hindi|Urdu|English)',
            r'Facebook.*?Twitter.*?Youtube.*?Instagram',
            r'©.*?Maulana Azad National Urdu University',
            r'Search form.*?Search',
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
            
        text = text.strip()
        
        if len(text) < 100:
            # Fallback to absolute raw if cleaning was too aggressive
            return soup.get_text(separator=' ', strip=True)[:max_chars]
            
        return text[:max_chars]
        
    except Exception as e:
        print(f"[web_fetcher] Critical failure for {url}: {e}")
        return None
