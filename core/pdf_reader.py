# core/pdf_reader.py
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import numpy as np
import cv2

def extract_text_from_pdf(file_path, ignore_titles=None):
    """
    Mengekstrak teks dari setiap halaman PDF menggunakan pendekatan hybrid.
    Jika sebuah halaman mengandung judul dari daftar ignore_titles,
    kontennya akan diabaikan (diganti dengan string kosong).
    """
    text_per_page = []
    
    try:
        images = convert_from_path(file_path, dpi=200)
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []

    with fitz.open(file_path) as doc:
        if len(images) != len(doc):
            print("Peringatan: Jumlah halaman dari PyMuPDF dan pdf2image tidak cocok.")
            return []
            
        for i, page in enumerate(doc):
            page_content = ""
            # 1. Coba ekstraksi teks digital
            text = page.get_text("text")
            
            # 2. Jika teks digital kosong atau sangat sedikit, gunakan OCR
            if not text or len(text.strip()) < 20:
                try:    
                    config = '--psm 6'
                    page_content = pytesseract.image_to_string(images[i], lang="ind+eng", config=config)
                except Exception:
                    page_content = "" # Abaikan jika ada error OCR
            else:
                page_content = text

            # 3. Periksa apakah halaman ini harus diabaikan
            if ignore_titles and any(title.lower() in page_content.lower() for title in ignore_titles):
                text_per_page.append("") # Tambahkan string kosong untuk mengabaikan halaman
            else:
                text_per_page.append(page_content)
    
    return text_per_page