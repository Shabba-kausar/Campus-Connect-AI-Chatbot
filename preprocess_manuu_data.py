import os
import glob
import re

def clean_text(text):
    # Remove extra whitespace, newlines, and non-informative lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = '\n'.join(lines)
    # Optionally, remove very short lines (like page numbers)
    cleaned = '\n'.join([line for line in cleaned.splitlines() if len(line) > 10])
    return cleaned

def combine_and_clean_text(input_dirs, output_file):
    all_text = []
    for input_dir in input_dirs:
        for fname in glob.glob(os.path.join(input_dir, '*.txt')):
            with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                cleaned = clean_text(text)
                all_text.append(cleaned)
    # Split into chunks (e.g., 500 words per chunk)
    combined = '\n'.join(all_text)
    words = combined.split()
    chunk_size = 500
    chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    with open(output_file, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(chunk + '\n---\n')
    print(f"Combined and cleaned data saved to {output_file}")

if __name__ == '__main__':
    combine_and_clean_text(['manuu_website_data', 'manuu_pdf_texts'], 'manuu_cleaned_chunks.txt')
