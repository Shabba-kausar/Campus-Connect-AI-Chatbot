import requests
from bs4 import BeautifulSoup
import os
import re

def get_all_links(base_url, section_paths):
    """Get all relevant links from given sections of the MANUU website."""
    all_links = set()
    for path in section_paths:
        url = base_url + path
        try:
            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/'):
                    href = base_url.rstrip('/') + href
                if href.startswith(base_url):
                    all_links.add(href)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    return list(all_links)

def save_page_text(url, out_dir):
    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Try to extract main content, fallback to all text
        main = soup.find('div', {'class': 'region region-content'})
        text = main.get_text(separator='\n', strip=True) if main else soup.get_text(separator='\n', strip=True)
        fname = re.sub(r'[^a-zA-Z0-9]', '_', url.replace('https://', '').replace('http://', ''))
        with open(os.path.join(out_dir, f'{fname}.txt'), 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Saved: {url}")
    except Exception as e:
        print(f"Failed to save {url}: {e}")

def main():
    base_url = 'https://manuu.edu.in'
    # Add more section paths as needed
    section_paths = [
        '/',
        '/admissions/',
        '/academics/',
        '/facilities/',
        '/departments/',
        '/student-support/',
        '/examinations/',
        '/notices/',
        '/events/',
    ]
    out_dir = 'manuu_website_data'
    os.makedirs(out_dir, exist_ok=True)
    links = get_all_links(base_url, section_paths)
    for url in links:
        save_page_text(url, out_dir)

if __name__ == '__main__':
    main()
