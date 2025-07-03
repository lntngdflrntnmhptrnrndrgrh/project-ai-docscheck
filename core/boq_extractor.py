# core/boq_extractor.py
import pandas as pd
import pytesseract
import re
from .checker import match_text_fuzzy

def re_extract_and_parse_boq(images):
    """
    Mengekstrak data BOQ dengan mencari designator dari kamus, dan sekarang juga
    mengembalikan nomor halaman tempat BOQ ditemukan.
    """
    KNOWN_DESIGNATORS = [
        "SC-OF-SM-24", "OS-SM-1", "ODP Solid-PB-8 AS", "PU-S9.0-140",
        "Slack Support HH", "Label Kabel Distribusi (KU FO)", "PU-S7.0-400NM",
        "AC-OF-SM-ADSS-120", "PU-ASDE--50/70", "PU-AS-SC"
    ]

    # --- PERUBAHAN 1: Gunakan enumerate untuk mendapatkan indeks halaman (i) ---
    for i, image in enumerate(images):
        try:
            ocr_df = pytesseract.image_to_data(image, lang="ind+eng", config="--psm 3", output_type=pytesseract.Output.DATAFRAME)
            ocr_df = ocr_df.dropna(subset=['text', 'conf']).copy()
            ocr_df['text'] = ocr_df['text'].astype(str)
            ocr_df = ocr_df[ocr_df.conf > 30]
        except Exception:
            continue

        page_text_for_check = " ".join(ocr_df['text']).lower()
        if "boq uji terima" not in page_text_for_check:
            continue

        ocr_df['line_group'] = (ocr_df['top'].diff().abs() > 10).cumsum()
        lines = ocr_df.groupby('line_group')['text'].apply(lambda x: ' '.join(x)).tolist()

        boq_data = []
        found_designators = set()

        for line in lines:
            for designator in KNOWN_DESIGNATORS:
                if designator not in found_designators and match_text_fuzzy(line, designator, threshold=0.7):
                    numbers_in_line = re.findall(r'\d+', line)
                    if numbers_in_line:
                        quantity = int(numbers_in_line[-1])
                        boq_data.append({
                            "DESIGNATOR": designator,
                            "KUANTITAS_BOQ": quantity
                        })
                        found_designators.add(designator)
                        break
        
        if boq_data:
            # --- PERUBAHAN 2: Kembalikan DataFrame DAN indeks halaman (i) ---
            return pd.DataFrame(boq_data), i

    # --- PERUBAHAN 3: Kembalikan None dan -1 jika tidak ditemukan ---
    return None, -1