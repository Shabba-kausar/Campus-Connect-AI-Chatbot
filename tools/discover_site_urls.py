import requests
import re
import os
import json
from urllib.parse import urljoin

homepage = 'https://manuu.edu.in/'

try:
    r = requests.get(homepage, timeout=15)
    r.raise_for_status()
    text = r.text
except Exception as e:
    print('Failed to fetch homepage:', e)
    text = ''

anchors = []
if text:
    anchors = re.findall(r'href\s*=\s*"([^"]+)"', text)
    anchors = list(dict.fromkeys(anchors))

candidates = []
for a in anchors:
    if a.startswith('/'):
        candidates.append(urljoin(homepage, a))
    elif a.startswith('http'):
        candidates.append(a)

# topics to find
topics = {
    'admission': 'admission',
    'courses': 'course',
    'hostel': 'hostel',
    'library': 'library',
    'placement': 'placement',
    'examination': 'exam',
    'contact': 'contact',
    'facilities': 'facility',
    'map': 'about'
}

# helper
def test_url_ok(u):
    try:
        h = requests.head(u, allow_redirects=True, timeout=8)
        if 200 <= h.status_code < 400:
            return True
    except Exception:
        pass
    try:
        g = requests.get(u, allow_redirects=True, timeout=8)
        if 200 <= g.status_code < 400:
            return True
    except Exception:
        pass
    return False

found = {}
for k in topics.keys():
    found_k = None
    mapped = None
    # look for candidates containing keyword
    for c in candidates:
        lk = c.lower()
        if k in lk or topics[k] in lk:
            if test_url_ok(c):
                found_k = c
                break
    if not found_k:
        # try looser matching
        for c in candidates:
            lk = c.lower()
            if topics[k] in lk or k in lk:
                if test_url_ok(c):
                    found_k = c
                    break
    if not found_k:
        found_k = homepage
    found[k] = found_k

# persist
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(data_dir, exist_ok=True)
target = os.path.join(data_dir, 'site_urls.json')
with open(target, 'w', encoding='utf-8') as f:
    json.dump(found, f, indent=2)

print(json.dumps(found, indent=2))
print('\nWrote to', target)
