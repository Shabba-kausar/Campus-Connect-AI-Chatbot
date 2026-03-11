import pdfplumber
import os
import glob

def extract_text_from_pdfs(pdf_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    pdf_files = glob.glob(os.path.join(pdf_dir, '*.pdf'))
    for pdf_file in pdf_files:
        try:
            with pdfplumber.open(pdf_file) as pdf:
                all_text = ''
                for page in pdf.pages:
                    all_text += page.extract_text() or ''
            fname = os.path.splitext(os.path.basename(pdf_file))[0] + '.txt'
            with open(os.path.join(out_dir, fname), 'w', encoding='utf-8') as f:
                f.write(all_text)
            print(f"Extracted: {pdf_file}")
        except Exception as e:
            print(f"Failed to extract {pdf_file}: {e}")

if __name__ == '__main__':
    # PDFs are saved in 'manuu_website_data' folder by the previous script
    extract_text_from_pdfs('manuu_website_data', 'manuu_pdf_texts')
