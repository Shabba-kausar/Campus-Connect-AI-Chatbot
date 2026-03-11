import re
from manuu_live_fetch import find_best_page_url, extract_main_text

# Topics to extract (Hyderabad campus only)
TOPICS = [
    {'name': 'Admission Process', 'keywords': ['admission', 'apply', 'application', 'regular', 'distance']},
    {'name': 'Hostel Details', 'keywords': ['hostel', 'boys hostel', 'girls hostel', 'accommodation', 'mess']},
    {'name': 'Canteen', 'keywords': ['canteen', 'cafeteria', 'food', 'mess']},
    {'name': 'Exam Dates', 'keywords': ['examination', 'exam', 'time table', 'timetable', 'schedule', 'notification']},
]

CHUNKS_FILE = 'manuu_chunks_index.txt'


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_topic_content_dynamic(keywords):
    try:
        # Find the best URL dynamically from the MANUU site
        # We join keywords into a pseudo-topic query by picking the first keyword
        topic_hint = keywords[0] if keywords else 'manuu'
        url = find_best_page_url(topic_hint)
        if not url:
            return ''
        text = extract_main_text(url)
        # Basic keyword filter
        for kw in keywords:
            if kw.lower() in text.lower():
                return clean_text(text)
        return clean_text(text)
    except Exception:
        return ''


def main():
    with open(CHUNKS_FILE, 'w', encoding='utf-8') as f:
        for topic in TOPICS:
            print(f"Extracting: {topic['name']}")
            content = extract_topic_content_dynamic(topic['keywords'])
            if content:
                chunk = f"**{topic['name']} (Hyderabad Campus)**: {content}"
                f.write(chunk + '\n')
            else:
                print(f"[Warning] No content found for {topic['name']}")

if __name__ == '__main__':
    main()
