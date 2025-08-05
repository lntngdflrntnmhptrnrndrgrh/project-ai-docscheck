# core/boq_extractor.py
import pytesseract
import pandas as pd
import cv2
import numpy as np
import re

def find_boq_page(images):
    """
    Mencari halaman BOQ yang benar dengan memeriksa kombinasi header kolom yang khas.
    """
    # Keyword utama yang kemungkinan besar ada di header tabel BOQ
    primary_keywords = ["uraian pekerjaan", "satuan"]
    # Keyword kuantitas (setidaknya salah satu harus ada)
    quantity_keywords = ["aktual", "actual", "volume", "jumlah"]

    for i, image in enumerate(images):
        try:
            # Lakukan OCR cepat untuk memeriksa konten halaman
            page_text = pytesseract.image_to_string(image, lang="ind+eng", config="--psm 3", timeout=12)
            page_text_lower = page_text.lower()

            # Kondisi Cerdas:
            # 1. Cek apakah SEMUA keyword utama ada di halaman ini.
            has_all_primary = all(keyword in page_text_lower for keyword in primary_keywords)
            
            # 2. Cek apakah SETIDAKNYA SATU keyword kuantitas ada.
            has_any_quantity = any(keyword in page_text_lower for keyword in quantity_keywords)

            # Halaman yang benar adalah yang memenuhi kedua kondisi di atas
            if has_all_primary and has_any_quantity:
                print(f"INFO: Halaman BOQ terdeteksi di halaman {i+1} berdasarkan kombinasi header.")
                return i
        except Exception as e:
            print(f"Error saat mencari halaman BOQ: {e}")
            continue
    
    print("PERINGATAN: Tidak ada halaman yang cocok dengan kombinasi header utama. Sistem akan mencoba mencari berdasarkan judul umum.")
    # Fallback jika kombinasi di atas tidak ditemukan
    for i, image in enumerate(images):
         try:
            page_text = pytesseract.image_to_string(image, lang="ind+eng", config="--psm 3", timeout=12)
            page_text_lower = page_text.lower()
            if "bill of quantity" in page_text_lower or "boq uji terima" in page_text_lower:
                print(f"INFO: Halaman BOQ terdeteksi di halaman {i+1} berdasarkan judul (fallback).")
                return i
         except Exception:
             continue

    # Jika semua metode gagal
    print("KESALAHAN: Halaman BOQ tidak dapat ditemukan di dalam dokumen.")
    return -1

def extract_boq_table_with_cv(images, boq_page_index):
    """
    Versi final yang paling disederhanakan dan fokus pada ekstraksi baris per baris 
    yang terbukti paling tangguh.
    """
    if boq_page_index == -1: 
        return pd.DataFrame()
    try:
        image_cv = np.array(images[boq_page_index].convert('RGB'))
        
        # 1. PRA-PEMROSESAN YANG PALING STABIL
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        scaled = cv2.resize(gray, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
        processed_image = cv2.adaptiveThreshold(scaled, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # 2. GUNAKAN OCR PALING DASAR (image_to_string) UNTUK MENGHINDARI KOMPLEKSITAS DATAFRAME
        ocr_config = r'--oem 3 --psm 4'
        ocr_text = pytesseract.image_to_string(processed_image, lang="ind+eng", config=ocr_config)

        # 3. LOGIKA EKSTRAKSI BARIS PER BARIS (PALING TANGGUH)
        boq_data = []
        lines = ocr_text.splitlines()
        unit_pattern = r'\b(pcs|unit|meter|core|pos|set|ls|buah)\b'
        
        for line in lines:
            if len(line) < 15 or "uraian pekerjaan" in line.lower():
                continue

            if re.search(unit_pattern, line, re.IGNORECASE):
                words = line.split()
                
                designator = ""
                # Cari kata pertama yang cocok dengan pola kode designator
                for word in words[:5]: # Cek 5 kata pertama
                    # Pola: Mengandung huruf DAN (angka ATAU '-') dan panjangnya > 2
                    if len(word) > 2 and re.search(r'[a-zA-Z]', word) and (re.search(r'\d', word) or '-' in word):
                        designator = word
                        break
                
                # Heuristik Kuantitas: Cari semua angka, ambil yang kedua dari terakhir
                numbers = [int(n.replace(',', '')) for n in re.findall(r'[\d,]+', line) if n.replace(',', '').isdigit()]
                
                quantity = 0
                if len(numbers) >= 2:
                    # Abaikan nomor urut di awal
                    first_word_is_num = words[0].replace('.', '').isdigit()
                    if first_word_is_num and int(words[0].replace('.', '')) == numbers[0]:
                        relevant_numbers = numbers[1:]
                    else:
                        relevant_numbers = numbers

                    if len(relevant_numbers) >= 2:
                        quantity = relevant_numbers[-2] # Ambil kedua dari terakhir sebagai AKTUAL
                    elif len(relevant_numbers) == 1:
                        quantity = relevant_numbers[0]

                if designator and quantity > 0:
                    boq_data.append({
                        "DESIGNATOR": designator.strip(' |[]().-:*'),
                        "KUANTITAS_BOQ": quantity
                    })

        return pd.DataFrame(boq_data).drop_duplicates() if boq_data else pd.DataFrame()

    except Exception as e:
        print(f"Error Kritis saat mengekstrak tabel BOQ: {e}")
        return pd.DataFrame()