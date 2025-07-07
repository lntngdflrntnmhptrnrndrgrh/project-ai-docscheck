# core/boq_extractor.py
import pytesseract

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