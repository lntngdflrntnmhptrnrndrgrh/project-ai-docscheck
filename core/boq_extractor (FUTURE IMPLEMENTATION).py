# core/boq_extractor.py
# Tidak perlu impor pytesseract atau pandas di sini lagi

#def find_boq_page_from_text(text_per_page):
#    """
#    Hanya mencari di halaman mana 'BOQ UJI TERIMA' berada dari list teks yang sudah ada.
#    Sangat cepat dan tidak melakukan OCR.
#    """
#    for i, page_text in enumerate(text_per_page):
#        if "boq uji terima" in page_text.lower():
#            return i # Kembalikan indeks halaman jika ditemukan
#    return -1 # Kembalikan -1 jika tidak ditemukan