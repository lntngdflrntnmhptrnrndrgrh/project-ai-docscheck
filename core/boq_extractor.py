# core/boq_extractor.py
import pytesseract
import re
import pandas as pd

def find_boq_page(images):
    """
    Memindai gambar untuk menemukan halaman yang berisi "BOQ UJI TERIMA".
    Mengembalikan nomor indeks halaman jika ditemukan, jika tidak -1.
    """
    for i, image in enumerate(images):
        try:
            # Lakukan OCR cepat untuk mencari judul
            page_text = pytesseract.image_to_string(image, lang="ind+eng", config="--psm 3", timeout=10)
            if "boq uji terima" in page_text.lower():
                return i
        except Exception:
            continue
    return -1

def extract_boq_table(images, boq_page_index):


    if boq_page_index == -1:
        return pd.DataFrame(columns=['DESIGNATOR', 'KUANTITAS_BOQ'])
    
    image = images[boq_page_index]

    try:
        ocr_df = pytesseract.image_to_data(image, lang="ind+eng", config="--psm 3", output_type=pytesseract.Output.DATAFRAME)
        ocr_df = ocr_df.dropna(subset=['text', 'conf'].copy())
        ocr_df['text'] = ocr_df['text'].astype(str)
        ocr_df = ocr_df[ocr_df.conf > 30]
    except Exception:
        return pd.DataFrame(columns=['DESIGNATOR', 'KUANTITAS_BOQ'])
    
    ocr_df['line_group'] = (ocr_df['top'].diff().abs() > 10).cumsum()
    lines = ocr_df.groupby('line_group')['text'].apply(lambda x: ' '.join(x)).tolist()

    boq_data = []
    pattern = re.compile(r"^\s*\d+\s+(.+?)\s+(?:pcs|unit|meter|core|pos|pes)\s+.*?\s+(\d+)\s*$", re.IGNORECASE)

    for line in lines:
        match = pattern.search(line)
        if match:
            designator = match.group(1).strip()
            quantity = int(match.group(2).strip())

            if "uraian" not in designator.lower() and "pekerjaan" not in designator.lower():
                boq_data.append({
                    "DESIGNATOR": designator,
                    "KUANTITAS_BOQ": quantity
                })

    if boq_data:
        return pd.DataFrame(boq_data).drop_duplicates().reset_index(drop=True)
    
    return pd.DataFrame(columns=['DESIGNATOR', 'KUANTITAS_BOQ'])