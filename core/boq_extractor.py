# core/boq_extractor.py
import pytesseract
import pandas as pd
import cv2
import numpy as np
import re

def find_and_extract_boq_with_cv(images):
    """
    Menggabungkan pipeline pra-pemrosesan gambar dengan parsing Regex cerdas
    untuk ekstraksi tabel BOQ yang akurat dan dinamis dalam satu fungsi.
    """
    for i, image in enumerate(images):
        try:
            # --- 1. PIPELINE PRA-PEMROSESAN GAMBAR (DARI KODE ANDA YANG BERHASIL) ---
            open_cv_image = np.array(image.convert('RGB'))
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
            processed_image = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

            # --- 2. LAKUKAN OCR PADA GAMBAR YANG SUDAH BERSIH ---
            ocr_text = pytesseract.image_to_string(processed_image, lang="ind+eng", config="--psm 3")
            
            # Cek apakah ini halaman BOQ dari teks yang sudah bersih
            if "boq uji terima" in ocr_text.lower():
                # --- 3. PARSING CERDAS DENGAN REGEX ---
                lines = ocr_text.splitlines()
                boq_data = []
                # Pola Regex ini menggunakan 'satuan' (pcs, unit, dll.) sebagai jangkar
                pattern = re.compile(r"^\s*\d+\s+(.+?)\s+(?:pcs|unit|meter|core|pos|pes)\s+.*?\s+(\d+)\s*$", re.IGNORECASE)
                
                for line in lines:
                    match = pattern.search(line)
                    if match:
                        # Grup 1 adalah Designator, Grup 2 adalah Kuantitas
                        designator = match.group(1).strip()
                        quantity = int(match.group(2).strip())
                        
                        # Filter tambahan untuk membuang baris header yang mungkin cocok
                        if "uraian" not in designator.lower() and "designator" not in designator.lower():
                            boq_data.append({"DESIGNATOR": designator, "KUANTITAS_BOQ": quantity})
                
                if boq_data:
                    # Kembalikan DataFrame dan indeks halaman jika berhasil
                    return pd.DataFrame(boq_data), i
                    
        except Exception as e:
            print(f"Error saat memproses halaman {i+1}: {e}")
            continue
            
    # Jika loop selesai tanpa menemukan BOQ
    return pd.DataFrame(columns=['DESIGNATOR', 'KUANTITAS_BOQ']), -1