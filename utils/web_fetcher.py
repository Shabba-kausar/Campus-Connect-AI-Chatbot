import requests
from bs4 import BeautifulSoup
import re

# A small helper that fetches a page and returns cleaned text
# Returns None on failure
# Enhanced to filter out navigation, headers, footers, and repetitive content

def fetch_from_web(url: str, max_chars: int = 2000) -> str | None:
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Remove script, style, and other non-content elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Remove common navigation and menu classes/ids
        for element in soup.find_all(class_=re.compile(r'nav|menu|sidebar|breadcrumb|footer|header', re.I)):
            element.decompose()
        
        for element in soup.find_all(id=re.compile(r'nav|menu|sidebar|breadcrumb|footer|header', re.I)):
            element.decompose()
        
        # Try to find main content area (common patterns)
        main_content = None
        for selector in ['main', 'article', '.content', '#content', '.main-content', '#main-content', '.page-content']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # Use main content if found, otherwise use body
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
        
        if not text:
            return None
        
        # Clean up excessive whitespace and remove repetitive patterns
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = re.sub(r'\n\s*\n', '\n', text)  # Remove multiple newlines
        
        # Remove common repetitive footer/header text patterns
        patterns_to_remove = [
            r'Skip to main content.*?Top',
            r'Language\s*:.*?(?:Hindi|Urdu|English)',
            r'Open configuration options.*?Configure block',
            r'Facebook.*?Twitter.*?Youtube.*?Instagram',
            r'Follow Us.*?Facebook.*?Twitter.*?Youtube.*?Instagram',
            r'Contact.*?FAQs.*?Website Policies',
            r'© Copyright.*?All Rights Reserved',
            r'Disclaimer\s*:.*?This website',
            r'Maulana Azad National Urdu University.*?MANUU',
            r'Home.*?About us.*?Academics.*?Administration',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove lines that are too short (likely navigation items or labels)
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 10]
        text = ' '.join(lines)
        
        # Remove excessive repetition of the same word/phrase
        words = text.split()
        if len(words) > 50:
            # Remove very short repetitive words that appear too frequently
            word_freq = {}
            for word in words:
                if len(word) > 2:
                    word_freq[word.lower()] = word_freq.get(word.lower(), 0) + 1
            
            # Filter out words that appear more than 20% of the time (likely navigation)
            threshold = len(words) * 0.2
            filtered_words = [w for w in words if word_freq.get(w.lower(), 0) < threshold]
            text = ' '.join(filtered_words)
        
        # Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        
        if not text or len(text) < 50:
            # If filtering removed too much, fall back to simpler extraction
            soup_fallback = BeautifulSoup(resp.text, 'html.parser')
            for script in soup_fallback(["script", "style"]):
                script.decompose()
            text = soup_fallback.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
        
        return text[:max_chars] if text else None
    except Exception as e:
        # Keep failures silent for production; print for local debugging
        print(f"[web_fetcher] fetch failed for {url}: {e}")
        return None
