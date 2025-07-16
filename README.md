# **AI DOCS CHECKER MENGGUNAKAN TESSERACT OCR**

## *Sistem ini masih dalam tahap pengembangan*

Cara Menggunakan Sistem Ini

**BUAT VIRTUAL ENVIRONMENT TERLEBIH DAHULU!**
```
1. python -m venv venv
2. ./venv/Scripts/activate
```
**INSTALL LIBRARY DAN SISTEM PENDUKUNG**
```
pip install -r requirements.txt
```

**JANGAN LUPA INSTALL POPPLER TERLEBIH DAHULU DAN MASUKKAN KE ENVIRONMENT VARIABLE**

**INSTALL TESSERACT OCR DAN MASUKKAN KE ENVIRONMENT VARIABLE (WINDOWS)**

Install tesseract terlebih dahulu di link berikut
[Tesseract OCR UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

Jangan lupa tambahkan tessdata Indonesian Language untuk hasil training OCR bahasa indonesia

Masukin ke path system di environment variables. Jika sudah, tutup VSCode & terminal/cmd lainnya, lalu buka lagi VSCode

Jalankan di terminal command **streamlit run app.py**
