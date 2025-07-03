# core/pdf_reader.py
import pytesseract
from pdf2image import convert_from_path
import fitz

def extract_text_from_pdf(file_path, ignore_titles=None):
    """
    Fungsi ini diekslusifkan untuk melakukan OCR pada halaman gambar dan mengekstrak teks digital.
    Fungsi ini akan mengembalikan teks per halaman dan juga list gambar untuk analisis lebih lanjut.
    """
    text_per_page = []
    images = []

    try:
        images = convert_from_path(file_path, dpi=200)
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        # Jika konversi gagal, buat list gambar kosong sesuai jumlah halaman
        with fitz.open(file_path) as doc:
            images = [None] * len(doc) 
    
    with fitz.open(file_path) as doc:
        # Pastikan jumlah gambar dan halaman cocok jika konversi berhasil
        if len(images) != len(doc):
             images = [None] * len(doc)

        for i, page in enumerate(doc):
            # Coba ekstraksi teks digital terlebih dahulu
            text = page.get_text("text")
            
            # Jika tidak ada teks digital, lakukan OCR pada gambar halaman tersebut
            if not text or len(text.strip()) < 20 and images[i] is not None:
                try:
                    # Gunakan config yang fleksibel untuk menangani berbagai jenis halaman
                    config = '--psm 6' 
                    page_content = pytesseract.image_to_string(images[i], lang="ind+eng", config=config)
                except Exception:
                    page_content = ""
            else:
                page_content = text if text else ""

            # Abaikan halaman berdasarkan judul yang ada di daftar ignore_titles
            if ignore_titles and any(title.lower() in page_content.lower() for title in ignore_titles):
                text_per_page.append("")
            else:
                text_per_page.append(page_content)

    # Kembalikan DUA variabel: list teks dan list gambar
    return text_per_page, images