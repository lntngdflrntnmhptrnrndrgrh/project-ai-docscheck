# app.py
import streamlit as st
import pandas as pd
from core.pdf_reader import extract_text_from_pdf
from core.checker import check_items
from collections import Counter
from datetime import datetime
from streamlit.components.v1 import html
from fpdf import FPDF
import io

st.set_page_config(page_title="Checklist Dokumen Internal", layout="wide")
st.title("📄 Checklist Verifikasi Dokumen Internal")

uploaded_file = st.file_uploader("Upload dokumen PDF", type="pdf")
if uploaded_file:
    file_path = f"data/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("File berhasil diupload!")
    
    # Definisikan judul halaman yang ingin diabaikan
    ignore_titles = ["CHECKLIST VERIFIKASI BA UJI TERIMA",
                     "CHECKLIST VERIFIKASI BERITA ACARA COMMISSIONING TEST"
                    ]

    # Tidak perlu ignore_titles lagi dengan logika checker yang baru
    text_per_page = extract_text_from_pdf(file_path, ignore_titles=ignore_titles)

    # Kata kunci pencarian yang diperbarui dan lebih akurat
    # Menggunakan list untuk memungkinkan beberapa kemungkinan judul per item
    checklist_items = {
        "Judul BAUT": ["DOKUMEN BERITA ACARA UJI TERIMA (BAUT-I)", "DOKUMEN BERITA ACARA UJI TERIMA"],
        "Daftar Hadir": ["DAFTAR HADIR UJI TERIMA"],
        "Surat Permintaan Uji Terima dari Mitra": ["Surat Permohonan UT"], # Mencari frasa spesifik
        "SK/Penunjukan Pelaksanaan Uji Terima": ["Penunjukan Personil Tim Uji Terima"], # Frasa ini tidak ada, jadi akan NOK
        "Nota Dinas Pelaksanaan Uji Terima": ["Nota Dinas Pelaksanaan Uji Terima"],
        "BOQ Uji Terima": ["BOQ UJI TERIMA"],
        "Foto Kegiatan Uji Terima": ["DOKUMENTASI UJI TERIMA"],
        "Foto Material terpasang sesuai BOQ": ["DOKUMENTASI INSTALASI", "DOKUMENTASI AKSESORIS TIANG"], # Judul yang mungkin relevan
        "Foto Roll Meter / Fault Locator": ["Fault Locator"], # Frasa ini tidak ada
        "Foto Pengukuran OPM": ["FOTO PENGUKURAN OPM", "FOTO PENGUKURAN OPM"],
        "Form OPM": ["FORM OPM", "DATA PENGUKURAN OPM"],
        "File PDF OTDR": ["OTDR Report", "HASIL UKUR OTDR"],
        "BA Lapangan": ["BA Lapangan"], # Frasa ini tidak ada
    }

    structured_items = [
        ("1", "A", "Judul BAUT"),
        ("1", "B", "Daftar Hadir"),
        ("2", "A", "Surat Permintaan Uji Terima dari Mitra"),
        ("3", "A", "SK/Penunjukan Pelaksanaan Uji Terima"),
        ("3", "B", "Nota Dinas Pelaksanaan Uji Terima"),
        ("4", "A", "BOQ Uji Terima"),
        ("4", "B", "Foto Kegiatan Uji Terima"),
        ("4", "C", "Foto Material terpasang sesuai BOQ"),
        ("4", "D", "Foto Roll Meter / Fault Locator"),
        ("4", "E", "Foto Pengukuran OPM"),
        ("4", "F", "Form OPM"),
        ("4", "G", "File PDF OTDR"),
        ("4", "H", "BA Lapangan")
    ]
    
    # Menggunakan structured_items untuk memastikan urutan yang benar
    item_keys_in_order = [item[2] for item in structured_items]
    check_results = check_items(checklist_items, text_per_page, item_keys_in_order)

    formatted_results = []
    for i, row in enumerate(check_results):
        no, sub, item = structured_items[i]

        # Format keterangan berdasarkan list 'Pages' yang diterima
        keterangan_text = "Item tidak ditemukan"
        if row["Pages"]: # Jika list tidak kosong
            # Ubah list angka menjadi string yang dipisahkan koma
            pages_str = ', '.join(map(str, row["Pages"]))
            keterangan_text = f"Ada di halaman {pages_str}"

        formatted_results.append({
            "No": no,
            "": sub,
            "ITEM YG DI PERIKSA": item,
            "STATUS OK": "✔" if row["Status"] == "OK" else "",
            "STATUS NOK": "✔" if row["Status"] == "NOK" else "",
            "KETERANGAN": keterangan_text # Menggunakan keterangan yang sudah di format
        })

    df = pd.DataFrame(formatted_results)
    no_counts = Counter([row["No"] for row in formatted_results])

    # --- Bagian HTML dan Download (tidak ada perubahan signifikan) ---
    table_html = """
    <style>
      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        font-family: "Inter", sans-serif;
        font-size: 14px;
        color: white;
      }
      th, td {
        border: 1px solid white;
        padding: 8px;
        text-align: center;
      }
      th {
        background-color: #444;
        color: white;
      }
      td.item-name {
        text-align: left;
      }
    </style>
    <table>
      <tr>
        <th rowspan="2">No</th>
        <th colspan="2">ITEM YG DI PERIKSA</th>
        <th colspan="2">STATUS</th>
        <th rowspan="2">KETERANGAN</th>
      </tr>
      <tr>
        <th> </th>
        <th style="text-align: left;"> </th>
        <th>OK</th>
        <th>NOK</th>
      </tr>
    """
    
    # Menggabungkan sel "No" dan "ITEM YG DI PERIKSA" dengan rowspan
    current_no = None
    for i in range(len(df)):
        row = df.iloc[i]
        table_html += "<tr>"
        if row['No'] != current_no:
            count = no_counts[row['No']]
            table_html += f'<td rowspan="{count}">{row["No"]}</td>'
            current_no = row['No']
        
        table_html += f"""
            <td>{row['']}</td>
            <td class="item-name">{row['ITEM YG DI PERIKSA']}</td>
            <td>{row['STATUS OK']}</td>
            <td>{row['STATUS NOK']}</td>
            <td>{row['KETERANGAN']}</td>
        </tr>
        """
    table_html += "</table>"

    st.subheader("Hasil Pengecekan")
    html(table_html, height=600, scrolling=True)

    st.subheader("Silahkan download hasil pengecekan dengan format Excel atau PDF")
    
    
    # Membuat file excel di dalam memori
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Hasil')
    excel_data = output_excel.getvalue()
    # Download dengan st.download_button
    st.download_button(
        label="Download Hasil berupa Excel",
        data=excel_data,
        file_name=f"hasil_cek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Membuat file PDF dan disimpan sebagai string di dalam memori
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Hasil Cek Kelengkapan Dokumen", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', size=11)
    # Header Tabel
    pdf.cell(10, 8, "No", border=1, align='C')
    pdf.cell(10, 8, "", border=1, align='C')
    pdf.cell(75, 8, "ITEM YANG DI PERIKSA", border=1, align='C')
    pdf.cell(15, 8, "OK", border=1, align='C')
    pdf.cell(15, 8, "NOK", border=1, align='C')
    pdf.cell(65, 8, "KETERANGAN", border=1, align='C')
    pdf.ln()
    # Isi Tabel
    pdf.set_font("Arial", size=10)
    prev_no = None
    for _, row in df.iterrows():
        no_cell = row["No"] if row["No"] != prev_no else ""
        prev_no = row["No"]
        pdf.cell(10, 8, no_cell, border=1, align='C')
        pdf.cell(10, 8, row[""], border=1, align='C')
        pdf.cell(75, 8, row["ITEM YG DI PERIKSA"], border=1,)
        pdf.cell(15, 8, "V" if row["STATUS OK"] else "", border=1, align='C')
        pdf.cell(15, 8, "V" if row["STATUS NOK"] else "", border=1, align='C')
        pdf.cell(65, 8, row["KETERANGAN"], border=1)
        pdf.ln()
    pdf_data = pdf.output(dest= 'S').encode('latin-1')
    st.download_button(
        label = "Download Hasil berupa PDF",
        data = pdf_data,
        file_name = f"hasil_cek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime = "application/pdf"
    )
