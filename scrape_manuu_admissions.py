import requests
from bs4 import BeautifulSoup

# Example: Scrape MANUU admissions page
url = "https://manuu.edu.in/admissions/"
response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    # Extract all text from the main content area
    main_content = soup.find('div', {'class': 'region region-content'})
    if main_content:
        text = main_content.get_text(separator='\n', strip=True)
        with open('manuu_admissions.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Admissions page content saved to manuu_admissions.txt")
    else:
        print("Main content area not found.")
else:
    print(f"Failed to fetch page: {response.status_code}")
