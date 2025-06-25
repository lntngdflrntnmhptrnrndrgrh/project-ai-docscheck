from pdf2image import convert_from_path
import os

PDF_DIR = "../data/"
OUTPUT_DIR = "../dataset_ttd_raw/"
POPPLER_PATH = r"C:\\poppler\\Library\\bin"  # Ubah sesuai OS kamu

os.makedirs(OUTPUT_DIR, exist_ok=True)

for file in os.listdir(PDF_DIR):
    if file.endswith(".pdf"):
        pdf_path = os.path.join(PDF_DIR, file)
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)

        for i, img in enumerate(images):
            name = f"{file[:-4]}_page{i+1}.png"
            img.save(os.path.join(OUTPUT_DIR, name))

print("✅ Semua PDF dikonversi menjadi gambar.")